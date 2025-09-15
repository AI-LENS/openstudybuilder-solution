import json
import os
from datetime import datetime
from typing import Any

from neomodel import db

from clinical_mdr_api import utils
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)
from common.config import settings

MATCH_SPECIFIC_STUDY_VERSION = """
    MATCH (sr:StudyRoot {uid: $study_uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(sv:StudyValue)
"""

MATCH_LATEST_STUDY = """
    MATCH (sr:StudyRoot {uid: $study_uid})-[:LATEST]->(sv:StudyValue)
"""


class QueryService:
    """class holding the queries for the listing endpoints."""

    @staticmethod
    def _filter_for_cdisc_ct(
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
    ) -> tuple[str, dict[Any, Any]]:
        """Create filter to use in cypher query"""
        filter_parameters = []
        filter_query_parameters = {}
        if catalogue_name:
            filter_by_catalogue = "toUpper(cat.name) in apoc.text.split(toUpper($catalogue_name), '[ ]*,[ ]*')"
            filter_parameters.append(filter_by_catalogue)
            filter_query_parameters["catalogue_name"] = catalogue_name
        if package:
            filter_by_package_name = "toUpper(package.name) in apoc.text.split(toUpper($package_name), '[ ]*,[ ]*')"
            filter_parameters.append(filter_by_package_name)
            filter_query_parameters["package_name"] = package
        if after_date:
            filter_by_after_date = """
                package.effective_date >= date($after_date)
            """
            filter_parameters.append(filter_by_after_date)
            filter_query_parameters["after_date"] = after_date

        filter_statements = " AND ".join(filter_parameters)
        filter_statements = (
            "WHERE " + filter_statements if len(filter_statements) > 0 else ""
        )
        return filter_statements, filter_query_parameters

    def get_metadata(self, dataset_name) -> list[Any]:
        """Get metadata for legacy (and other) datasets"""

        with open(
            os.getcwd() + "/clinical_mdr_api/listings/metadata.json",
            "r",
            encoding="UTF-8",
        ) as metadata:
            meta = json.load(metadata)

        if dataset_name:
            meta = [
                x
                for x in meta
                if x["dataset_name"] in dataset_name.replace(" ", "").lower().split(",")
            ]

        return meta

    def get_topic_codes(
        self,
        at_specific_date: datetime | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset topic_cd_def."""

        match_clause = """
            MATCH (r:ActivityInstanceRoot)-[l]->(n:ActivityInstanceValue) 
            """

        if at_specific_date:
            filter_query = """
                WHERE (type(l)='HAS_VERSION' and l.status='Final'
                      and l.start_date < datetime($at_specific_date) <= l.end_date)
            """
        else:
            filter_query = """
                WHERE type(l)='LATEST_FINAL'
            """

        alias_clause = """
        
              n.name                       as lb,
              n.topic_code                 as topic_cd,
              n.adam_param_code            as short_topic_cd,
              coalesce(n.is_required_for_activity, false)   as is_required_for_activity,
              coalesce(n.is_default_selected_for_activity, false) as is_default_selected_for_activity,
              coalesce(n.is_data_sharing, false) as is_data_sharing,
              coalesce(n.is_legacy_usage, false) as is_legacy_usage,
              n.legacy_description         as description,
              n.molecular_weight           as molecular_weight,
              n.value_sas_display_format   as sas_display_format,
             CASE
              WHEN (n:FindingValue) THEN 'Findings'
              WHEN (n:InterventionValue) THEN 'Interventions'
              WHEN (n:EventValue) THEN 'Events'
              ELSE 'Other'
             END as general_domain_class,
             CASE
              WHEN (n:NumericFindingValue) THEN 'NumericFinding'
              WHEN (n:CategoricFindingValue) THEN 'CategoricFinding'
              WHEN (n:TextualFindingValue) THEN 'TextualFinding'
              WHEN (n:CompoundDosingValue) THEN 'CompoundDosing'
              ELSE 'Other'
             END as sub_domain_class,
             CASE
              WHEN (n:CompoundValue) THEN 'Compound'
              WHEN (n:LaboratoryActivityValue) THEN 'LaboratoryActivity'
              WHEN (n:RatingScaleValue) THEN 'RatingScale'
              ELSE 'Other'
             END as sub_domain_type
            ORDER BY n.name
                   
              
            """
        match_clause = match_clause + filter_query

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        if at_specific_date:
            query.parameters.update({"at_specific_date": at_specific_date})
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_ver(
        self,
        catalogue_name: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_ver."""

        match_clause = """
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
            """
        alias_clause = """
             cat.name as ct_scope, 
             toString(date(package.effective_date)) as ct_ver,
             package.name as pkg_nm
             
            """
        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()
        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_pkg(
        self,
        catalogue_name: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_pkg."""

        match_clause = """
               MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]->(package:CTPackage)
               """
        alias_clause = """
            cat.name as pkg_scope,
            package.name as pkg_nm
            """
        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_list(
        self,
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_list."""

        match_clause = """
        
            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]-> (package:CTPackage)-[:CONTAINS_CODELIST]
            -> (package_codelist:CTPackageCodelist)-[:CONTAINS_ATTRIBUTES]
            -> (codelist_attributes_value:CTCodelistAttributesValue)
            """

        alias_clause = """
             
            replace(package_codelist.uid,package.uid+'_','')        as ct_cd_list_cd, 
            CASE codelist_attributes_value.extensible
              WHEN false THEN 'N'
              WHEN true THEN 'Y'
            END                                                         as ct_cd_list_extensible,
            codelist_attributes_value.name                              as ct_cd_list_nm,
            codelist_attributes_value.submission_value                  as ct_cd_list_submval,
            cat.name                                                    as ct_scope,
            toString(date(package.effective_date))                      as ct_ver,
            codelist_attributes_value.definition                        as definition,
            codelist_attributes_value.preferred_term                    as nci_pref_term,
            package.name                                                as pkg_nm,
            apoc.text.join(codelist_attributes_value.synonyms,';')      as synonyms
            """

        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, package=package, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn(items=result, total=total)

    def get_cdisc_ct_val(
        self,
        catalogue_name: str | None = None,
        package: str | None = None,
        after_date: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """Query to get the legacy dataset cdisc_ct_val."""

        match_clause = """

            MATCH (cat:CTCatalogue)-[:CONTAINS_PACKAGE]-> (package:CTPackage)-[:CONTAINS_CODELIST]
            -> (package_codelist:CTPackageCodelist)-[:CONTAINS_TERM] -> (:CTPackageTerm)-[:CONTAINS_ATTRIBUTES]
            -> (term_attributes_value:CTTermAttributesValue)
            MATCH (package_codelist)-[:CONTAINS_ATTRIBUTES]-> (codelist_attributes_value:CTCodelistAttributesValue)
            """

        alias_clause = """

            term_attributes_value.concept_id                    as ct_cd,
            codelist_attributes_value.submission_value          as ct_cd_list_submval,
            cat.name                                            as ct_scope,
            term_attributes_value.code_submission_value         as ct_submval,
            toString(date(package.effective_date))              as ct_ver,
            term_attributes_value.definition                    as definition,
            term_attributes_value.preferred_term                as nci_pref_term,
            package.name                                        as pkg_nm,
            apoc.text.join(term_attributes_value.synonyms,';')  as synonyms

            """

        # get filters and update match clause
        filter_statements, filter_query_parameters = self._filter_for_cdisc_ct(
            catalogue_name=catalogue_name, package=package, after_date=after_date
        )
        match_clause += filter_statements

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        res = (result_array, attributes_names)
        result = utils.db_result_to_list(res)

        total = 0
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]

        return GenericFilteringReturn(items=result, total=total)

    def get_tv(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        // Query to retrieve TV data from the Study Visit table
        // We are looking for the latest visit name, study day, and study week values associated with a specific study value version or all (latest) study versions.
        // The query filters by domain (TV), selecting the 'StudID', 'VisitNum', 'StudyDayValue' (or 'StudyWeekValue'), 'ArmCD', 'Arm', and any other fields we want to include.
        // We use optional matches for the visit name, day, and week to avoid errors in case these fields are missing. We also add a condition to handle the situation when only one of these fields is present.
        MATCH (sv)-[:HAS_STUDY_VISIT]->(v:StudyVisit)
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST]->(nv:VisitNameValue),
                        (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue),
                        (v)-->(wr:StudyWeekRoot)-[:LATEST]->(wv:StudyWeekValue)
        OPTIONAL MATCH (udv:UnitDefinitionValue)-[:LATEST_FINAL]-(udr:UnitDefinitionRoot)--(stf:StudyTimeField)--(sv)
            WHERE stf.field_name = "soa_preferred_time_unit"

        RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TV' AS DOMAIN,
            toInteger(v.unique_visit_number) AS VISITNUM,
            CASE
                // WEEK
                WHEN udv.name = "week" THEN toUpper(nv.name + " (" +udv.name + " "+toInteger(wv.value)+")")
                // DAY
                WHEN udv.name = "day" THEN toUpper(nv.name + " (" +udv.name + " "+toInteger(dv.value)+")")
            ELSE toUpper(nv.name)
            END AS VISIT,
            toInteger(dv.value) AS VISITDY,
            NULL AS ARMCD,
            NULL AS ARM,
            toUpper(v.start_rule) AS TVSTRL,
            toUpper(v.end_rule) AS TVENRL
        ORDER BY v.unique_visit_number;
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_mdvisit(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        MATCH (sv)-[:HAS_STUDY_VISIT]->(v:StudyVisit)
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST]->(nv:VisitNameValue)
        OPTIONAL MATCH  (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue)
        OPTIONAL MATCH  (v)-->(wr:StudyWeekRoot)-[:LATEST]->(wv:StudyWeekValue)
        OPTIONAL MATCH  (v)-[:HAS_VISIT_TYPE]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]-(vtnv:CTTermNameValue)
        OPTIONAL MATCH (udv:UnitDefinitionValue)-[:LATEST_FINAL]-(udr:UnitDefinitionRoot)--(stf:StudyTimeField)--(sv)
            WHERE stf.field_name = "soa_preferred_time_unit"
        RETURN
            toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            toInteger(v.unique_visit_number) AS VISIT_NUM,
            toUpper(nv.name) AS VISIT_NAME,
            CASE
                // WEEK
                WHEN udv.name = "week" THEN nv.name + " (" +udv.name + " "+toInteger(wv.value)+")"
                // DAY
                WHEN udv.name = "day" THEN nv.name + " (" +udv.name + " "+toInteger(dv.value)+")"
            ELSE NULL
            END AS AVISIT,
            toInteger(dv.value) AS DAY_VALUE,
            v.short_visit_label as VISIT_SHORT_LABEL,
            dv.name AS DAY_NAME,
            wv.name AS WEEK_NAME,
            toInteger(wv.value) AS WEEK_VALUE,
            vtnv.name as VISIT_TYPE_NAME
        ORDER BY VISIT_NUM;
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_mdflow(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        MATCH (sv)--(sact_schedule:StudyActivitySchedule)
        MATCH (sact_schedule)--(v:StudyVisit)--(sv)
        OPTIONAL MATCH (v)-[:HAS_VISIT_TYPE]-(:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST_FINAL]-(ctterm_name_value_visit_type:CTTermNameValue)
            where v.is_global_anchor_visit = True
        OPTIONAL MATCH  (v)-->(nr:VisitNameRoot)-[:LATEST_FINAL]->(nv:VisitNameValue)
        MATCH (sact_schedule)--(sact:StudyActivity)--(sv)
        OPTIONAL MATCH (sact)--(sactins:StudyActivityInstance)--(sv)
        OPTIONAL MATCH (sactins)--(act_inst_value:ActivityInstanceValue)
        OPTIONAL MATCH (act_inst_value)-[:ACTIVITY_INSTANCE_CLASS]-(aicr:ActivityInstanceClassRoot)-[:LATEST_FINAL]-(aicv:ActivityInstanceClassValue)
            WHERE aicv.name = "NumericFinding" 
                OR aicv.name = "CategoricFinding" 
                OR aicv.name = "TextualFinding" 

        OPTIONAL MATCH (act_inst_value:ActivityInstanceValue)--(act_item:ActivityItem)--(unit_definition_root:UnitDefinitionRoot)-[:LATEST]-(unit_definition_value:UnitDefinitionValue)
            WHERE aicv.name = "NumericFinding" 

        OPTIONAL MATCH  (v)-->(dr:StudyDayRoot)-[:LATEST]->(dv:StudyDayValue)
        OPTIONAL MATCH  (v)-->(wr:StudyWeekRoot)-[:LATEST]->(wv:StudyWeekValue)
        OPTIONAL MATCH (udv:UnitDefinitionValue)-[:LATEST_FINAL]-(udr:UnitDefinitionRoot)--(stf:StudyTimeField)--(sv)
            WHERE stf.field_name = "soa_preferred_time_unit"
        WITH  toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID_FLOWCHART,
            v.unique_visit_number AS AVISITN,
            act_inst_value.adam_param_code AS PARAMCD,
            CASE 
                // WEEK
                WHEN udv.name = "week" THEN nv.name + " (" +udv.name + " "+toInteger(wv.value)+")"
                // DAY
                WHEN udv.name = "day" THEN nv.name + " (" +udv.name + " "+toInteger(dv.value)+")"
            ELSE NULL
            END AS AVISIT,
            CASE 
                WHEN (NOT aicv IS NULL) THEN 
                    CASE 
                        WHEN aicv.name = "NumericFinding" AND NOT unit_definition_value IS NULL THEN act_inst_value.adam_param_code+" ("+unit_definition_value.name+")"
                    ELSE act_inst_value.adam_param_code
                    END
                ELSE NULL
            END AS PARAM,
            sact.order AS PARAMN,
            NULL AS ATPTN,
            NULL AS ATPT,
            act_inst_value.topic_code AS TOPICCD,
            CASE 
                WHEN v.is_global_anchor_visit THEN ctterm_name_value_visit_type.name 
                ELSE NULL
            END AS BASETYPE,
            CASE
                WHEN v.is_global_anchor_visit THEN "Y"
                ELSE NULL
            END AS ABLFL,
            ctterm_name_value_visit_type.name AS ASSMTYPE
        RETURN distinct  STUDYID_FLOWCHART,
            AVISITN,
            PARAMCD,
            AVISIT,
            PARAM,
            PARAMN,
            ATPTN,
            ATPT,
            TOPICCD,
            BASETYPE,
            ABLFL,
            ASSMTYPE
        ORDER BY STUDYID_FLOWCHART, AVISITN, PARAMN;
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_mdendpnt(
        self,
        study_uid: str,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = "MATCH (s_r:StudyRoot {uid: $study_uid})-[l:HAS_VERSION{status:'RELEASED', version:$study_value_version}]->(s_v:StudyValue) "
        else:
            query = (
                "MATCH (s_r:StudyRoot {uid: $study_uid})-[:LATEST]->(s_v:StudyValue)"
            )
        query = (
            query
            + """
        MATCH (s_v)-[:HAS_STUDY_OBJECTIVE]-(s_obj:StudyObjective)
        // fetch objective data
        OPTIONAL MATCH (s_obj)-[:HAS_OBJECTIVE_LEVEL]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(obj_lev:CTTermNameValue)
        OPTIONAL MATCH (s_obj)-[:HAS_SELECTED_OBJECTIVE]->(obj_val:ObjectiveValue)<--(obj_roo:ObjectiveRoot)
        OPTIONAL MATCH (s_obj)<-[:STUDY_ENDPOINT_HAS_STUDY_OBJECTIVE]-(s_end:StudyEndpoint)<-[:HAS_STUDY_ENDPOINT]-(s_v)
        // fetch endpoint data
        OPTIONAL MATCH (s_end)-[:HAS_ENDPOINT_LEVEL]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(end_lev:CTTermNameValue)
        OPTIONAL MATCH (s_end)-[:HAS_ENDPOINT_SUB_LEVEL]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(end_sublev:CTTermNameValue)
        OPTIONAL MATCH (s_end)-[:HAS_SELECTED_ENDPOINT]->(end_val:EndpointValue)<--(end_roo:EndpointRoot)
        OPTIONAL MATCH (s_end)-[:HAS_UNIT]->(:UnitDefinitionRoot)-[:LATEST]->(uni_value:UnitDefinitionValue)-[:HAS_CT_UNIT]->(uni_ctt_roo:CTTermRoot)
        OPTIONAL MATCH (s_end)-[:HAS_SELECTED_TIMEFRAME]->(tim_fra_val:TimeframeValue)<--(tim_fra_roo:TimeframeRoot)
        // fetch any Activities instantiated in ObjectiveTemplate or EndpointTemplate
        OPTIONAL MATCH (study_end_obj)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t:TemplateParameter)
            WHERE t.name IN ["Activity"] AND (study_end_obj = s_obj OR study_end_obj = s_end)
        OPTIONAL MATCH (study_end_obj2)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_subgroup_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t2:TemplateParameter)
            WHERE t2.name IN ['ActivitySubGroup'] AND (study_end_obj2 = s_obj OR study_end_obj2 = s_end)
        OPTIONAL MATCH (study_end_obj3)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_group_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t3:TemplateParameter)
            WHERE t3.name IN [ "ActivityGroup"] AND (study_end_obj3 = s_obj OR study_end_obj3 = s_end)
        OPTIONAL MATCH (study_end_obj4)-[:HAS_SELECTED_ENDPOINT|HAS_SELECTED_OBJECTIVE|HAS_SELECTED_TIMEFRAME]->(:SyntaxInstanceValue)-[:USES_VALUE]->(activity_instance_tem_par_root)<-[:HAS_PARAMETER_TERM]-(t4:TemplateParameter)
            WHERE t4.name IN ['ActivityInstance'] AND (study_end_obj4 = s_obj OR study_end_obj4 = s_end)
        OPTIONAL MATCH (activity_tem_par_root)-[:LATEST]->(activity_tem_par_value)
        OPTIONAL MATCH (activity_subgroup_tem_par_root)-[:LATEST]->(activity_subgroup_tem_par_value)
        OPTIONAL MATCH (activity_group_tem_par_root)-[:LATEST]->(activity_group_tem_par_value)
        OPTIONAL MATCH (activity_instance_tem_par_root)-[:LATEST]->(activity_instance_tem_par_value)
        WITH 
            s_r, 
            s_v, 
            s_obj, 
            obj_lev,
            obj_val,
            obj_roo,
            s_end,
            end_lev,
            end_sublev,
            end_val,
            end_roo,
            uni_value,
            uni_ctt_roo,
            tim_fra_val,
            tim_fra_roo,
            COLLECT(DISTINCT activity_tem_par_value.name) as activity_tem_par_root_uid_collected,
            COLLECT(DISTINCT activity_subgroup_tem_par_value.name) as activity_subgroup_tem_par_root_uid_collected,
            COLLECT(DISTINCT activity_group_tem_par_value.name) as activity_group_tem_par_root_uid_collected,
            COLLECT(DISTINCT activity_instance_tem_par_value.name) as activity_instance_tem_par_root_uid_collected
        return 
            DISTINCT s_r.uid as STUDYID_OBJ, 
            obj_lev.name AS OBJTVLVL,
            obj_val.name AS OBJTV,
            obj_val.name_plain AS OBJTVPT,
            end_lev.name AS ENDPNTLVL,
            end_sublev.name AS ENDPNTSL,
            end_val.name AS  ENDPNT, 
            end_val.name_plain AS ENDPNTPT, 
            uni_value.definition AS UNITDEF,
            uni_ctt_roo.uid AS UNIT,
            tim_fra_val.name AS TMFRM,
            tim_fra_val.name_plain AS TMFRMPT,
            activity_tem_par_root_uid_collected AS RACT,
            activity_subgroup_tem_par_root_uid_collected AS RACTSGRP,
            activity_group_tem_par_root_uid_collected AS RACTGRP,
            activity_instance_tem_par_root_uid_collected AS RACTINST
        ORDER BY STUDYID_OBJ, OBJTV, ENDPNT, TMFRM
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_ta(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        MATCH (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement)
        CALL 
            {
            WITH sv, se
            MATCH (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_ARM] -(sar:StudyArm)-[:STUDY_ARM_HAS_DESIGN_CELL]-(sd)
            OPTIONAL MATCH (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
                'TA' AS DOMAIN,
                se.name AS ELEMENT,
                se.order AS ETCD,
                sep.order as TAETORD,
                sd.transition_rule AS TATRANS,
                sep_term.name AS EPOCH,
                sar.name AS ARM,
                CASE  
                    WHEN sba.branch_arm_code IS NULL THEN sar.arm_code  
                    ELSE sar.arm_code+'-'+ sba.branch_arm_code 
                END AS ARMCD,
                sba.name AS TABRANCH
                ORDER BY sar.order, sep.order
            union all
            WITH sv, se
            MATCH (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(sv),
            (sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd),
            (sba)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar:StudyArm)-[:HAS_STUDY_ARM]-(sv)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            RETURN toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
                'TA' AS DOMAIN,
                se.name AS ELEMENT,
                se.order AS ETCD,
                sep.order as TAETORD,
                sd.transition_rule AS TATRANS,
                sep_term.name AS EPOCH,
                sar.name AS ARM,
                CASE 
                    WHEN sba.branch_arm_code IS NULL THEN sar.arm_code  
                    ELSE sar.arm_code+'-'+ sba.branch_arm_code 
                END AS ARMCD,
                sba.name AS TABRANCH
        }
        RETURN 
            STUDYID,
            DOMAIN,
            ELEMENT,
            ETCD,
            TAETORD,
            TATRANS,
            EPOCH,
            ARM, 
            ARMCD,
            TABRANCH
        ORDER BY ARMCD, TAETORD
            


        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_ti(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        MATCH (sv)-->(sc:StudyCriteria)
        MATCH (sc)-->(cv:CriteriaValue)<-[:LATEST]-(cr:CriteriaRoot)<--(ctr:CriteriaTemplateRoot)-->(i:CTTermRoot)-->(atr:CTTermAttributesRoot)-[:LATEST]->(atv:CTTermAttributesValue)
        WHERE atv.concept_id = 'C25532' or atv.concept_id = 'C25370'
        RETURN  toUpper(sv.study_id_prefix) + '-' + toUpper(sv.study_number) AS STUDYID,
                'TI' AS DOMAIN,
                TOUPPER(substring(atv.code_submission_value,0,1)) + toInteger(sc.order) AS IETESTCD,
                cv.name_plain AS IETEST,
                atv.code_submission_value AS IECAT,
                '' AS IESCAT,
                '' AS TIRL,
                '' AS TIVERS
        ORDER BY IETESTCD;
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_ts(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + f"""
        WITH sr, sv
        CALL {{
        WITH sr, sv
        MATCH (sv)-->(sf:StudyField)
        OPTIONAL MATCH  (sf)-->(ctr:CTTermRoot)-->(ctar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ctav:CTTermAttributesValue)<--(:CTPackageTerm)<--(:CTPackageCodelist)<--(ctp:CTPackage)
        OPTIONAL MATCH (sf)-->(dtr:DictionaryTermRoot)-->(dtv:DictionaryTermValue)
        OPTIONAL MATCH (sf)-[:HAS_REASON_FOR_NULL_VALUE]->(ct_null:CTTermRoot{{uid:'{settings.ct_uid_na_value}'}})
        OPTIONAL MATCH (sf)-[:HAS_REASON_FOR_NULL_VALUE]->(ct_pinf:CTTermRoot{{uid:'{settings.ct_uid_positive_infinity}'}})
        WITH *,
        CASE sf.field_name
            WHEN 'disease_condition_or_indication_codes' THEN 'C112038_INDIC'
            WHEN 'stratification_factor' THEN 'C16153_STRATFCT'
            WHEN 'stable_disease_minimum_duration' THEN 'C98783_SDMDUR'
            WHEN 'relapse_criteria' THEN 'C117961_RLPSCRIT'
            WHEN 'eudract_id' THEN 'C98714_REGID'
            WHEN 'ct_gov_id' THEN 'C98714_REGID'
            WHEN 'universal_trial_number_utn' THEN 'C98714_REGID'
            WHEN 'investigational_new_drug_application_number_ind' THEN 'C98714_REGID'
            WHEN 'japanese_trial_registry_id_japic' THEN 'C98714_REGID'
            WHEN 'eu_trial_number' THEN 'C98714_REGID'
            WHEN 'civ_id_sin_number' THEN 'C98714_REGID'
            WHEN 'national_clinical_trial_number' THEN 'C98714_REGID'
            WHEN 'japanese_trial_registry_number_jrct' THEN 'C98714_REGID'
            WHEN 'national_medical_products_administration_nmpa_number' THEN 'C98714_REGID'
            WHEN 'eudamed_srn_number' THEN 'C98714_REGID'
            WHEN 'investigational_device_exemption_ide_number' THEN 'C98714_REGID'
            WHEN 'confirmed_response_minimum_duration' THEN 'C98715_CRMDUR'
            WHEN 'is_adaptive_design' THEN 'C146995_ADAPT'
            WHEN 'study_stop_rules' THEN 'C49698_STOPRULE'
            WHEN 'trial_phase_code' THEN 'C48281_TPHASE'
            WHEN 'rare_disease_indicator' THEN 'C126070_RDIND'
            WHEN 'study_title' THEN 'C49802_TITLE'
            WHEN 'study_type_code' THEN 'C142175_STYPE'
            WHEN 'trial_type_codes' THEN 'C49660_TTYPE'
            WHEN 'is_extension_trial' THEN 'C139274_EXTTIND'
            WHEN 'healthy_subject_indicator' THEN 'C98737_HLTSUBJI'
            WHEN 'pediatric_investigation_plan_indicator' THEN 'C126069_PIPIND'
            WHEN 'pediatric_study_indicator' THEN 'C123632_PDSTIND'
            WHEN 'pediatric_postmarket_study_indicator' THEN 'C123631_PDPSTIND'
            WHEN 'therapeutic_area_codes' THEN 'C101302_THERAREA'
            WHEN 'diagnosis_group_codes' THEN 'C49650_TDIGRP'
            WHEN 'sex_of_participants_code' THEN 'C49696_SEXPOP'
            WHEN 'planned_maximum_age_of_subjects' THEN 'C49694_AGEMAX'
            WHEN 'planned_minimum_age_of_subjects' THEN 'C49693_AGEMIN'
            WHEN 'number_of_expected_subjects' THEN 'C49692_PLANSUB'
            WHEN 'control_type_code' THEN 'C49647_TCNTRL'
            WHEN 'trial_blinding_schema_code' THEN 'C49658_TBLIND'
            WHEN 'intervention_model_code' THEN 'C98746_INTMODEL'
            WHEN 'is_trial_randomised' THEN 'C25196_RANDOM'
            WHEN 'add_on_to_existing_treatments' THEN 'C49703_ADDON'
            WHEN 'trial_intent_types_codes' THEN 'C49652_TINDTP'
            WHEN 'planned_study_length' THEN 'C49697_LENGTH'
            WHEN 'intervention_type_code' THEN 'C98747_INTTYPE'
        END AS term_uid,
        CASE
            // for StudyTimeFields and StudyIntFields we want to display
            // actual value that is stored in the StudyField node
            WHEN sf.field_name='eudract_id' THEN 'EUDRACT'
            WHEN sf.field_name='ct_gov_id' THEN 'ClinicalTrials.gov'
            WHEN sf.field_name='universal_trial_number_utn' THEN 'UTN'
            WHEN sf.field_name='investigational_new_drug_application_number_ind' THEN 'IND'
            WHEN sf.field_name='japanese_trial_registry_id_japic' THEN 'JAPIC'
            WHEN sf.field_name='eu_trial_number' THEN 'ETN'
            WHEN sf.field_name='civ_id_sin_number' THEN 'CISN'
            WHEN sf.field_name='national_clinical_trial_number' THEN 'NCTN'
            WHEN sf.field_name='japanese_trial_registry_number_jrct' THEN 'JRCT'
            WHEN sf.field_name='national_medical_products_administration_nmpa_number' THEN 'NMPA'
            WHEN sf.field_name='eudamed_srn_number' THEN 'ESN'
            WHEN sf.field_name='investigational_device_exemption_ide_number' THEN 'IDE'
            WHEN sf:StudyTimeField
                THEN 'Not Controlled TimeField'
            WHEN sf:StudyIntField
                THEN 'Not Controlled IntField'
            WHEN ctr IS NOT NULL
                THEN 'CDISC'
            WHEN dtv IS NOT NULL
                THEN 'Dictionary'
            ELSE 'Not Controlled'
        END AS controlled_by
        MATCH (tr:CTTermRoot {{uid:term_uid}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        RETURN DISTINCT 
        sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        tav.code_submission_value AS TSPARMCD,
        tav.name_submission_value AS TSPARM,
        controlled_by AS controlled_by,
        CASE
        WHEN controlled_by = 'CDISC' AND ct_null IS NULL THEN ctav.code_submission_value
        WHEN controlled_by = 'Dictionary' THEN dtv.name
        WHEN sf.value = [] THEN NULL
        ELSE sf.value
        END AS TSVAL,
        CASE 
            WHEN ct_null IS NOT NULL THEN 'NA'
            WHEN controlled_by = 'Not Controlled TimeField' AND ct_pinf IS NOT NULL THEN 'PINF'
            ELSE ''
        END AS TSVALNF,
        CASE 
        WHEN controlled_by = 'CDISC' AND ct_null IS NULL  THEN ctr.concept_id
        WHEN controlled_by = 'Dictionary' THEN dtv.dictionary_id
        ELSE ''
        END AS TSVALCD,
        CASE
        WHEN controlled_by = 'Not Controlled TimeField' THEN 'ISO8601'
        WHEN controlled_by = 'CDISC' AND ct_null IS NULL  THEN 'CDISC'
        WHEN controlled_by = 'Dictionary' THEN head([(library:Library)-[:CONTAINS_DICTIONARY_TERM]->(dtr) | library.name])
        WHEN controlled_by IN ['EUDRACT', 'ClinicalTrials.gov', 'UTN', 'IND', 'JAPIC', 'ETN', 'CISN', 'NCTN', 'JRCT', 'NMPA', 'ESN', 'IDE'] THEN controlled_by
        ELSE ''
        END AS TSVCDREF,
        '' AS TSVCDVER
        UNION
        WITH sr, sv
        MATCH (sv)-[:HAS_STUDY_OBJECTIVE]->(so:StudyObjective)-[:HAS_OBJECTIVE_LEVEL]->(objlv)-->(octar:CTTermAttributesRoot)-[:LATEST_FINAL]->(octav:CTTermAttributesValue)
        MATCH (so)-[:HAS_SELECTED_OBJECTIVE]->(obj)
        RETURN
        sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        octav.code_submission_value AS TSPARMCD,
        octav.name_submission_value AS TSPARM,
        '' AS controlled_by,
        obj.name_plain AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER
        UNION
        WITH sr, sv
        MATCH (sv)-[:HAS_STUDY_ENDPOINT]->(send)-[:HAS_ENDPOINT_LEVEL]->(endplv)-->(ectar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ectav:CTTermAttributesValue) 
        MATCH (send)-[:HAS_SELECTED_TIMEFRAME]->(tf:TimeframeValue)
        MATCH (send)-[:HAS_SELECTED_ENDPOINT]->(endp:EndpointValue)
        OPTIONAL MATCH (send)-[:HAS_ENDPOINT_SUB_LEVEL]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(:CTTermNameRoot)-[:LATEST]->(end_sublev:CTTermNameValue)
        OPTIONAL MATCH (send)-[:HAS_SELECTED_ENDPOINT]->(end_val:EndpointValue)<--(end_roo:EndpointRoot)
        OPTIONAL MATCH (send)-[:HAS_UNIT]->(:UnitDefinitionRoot)-[:LATEST]->(uni_value:UnitDefinitionValue)-[:HAS_CT_UNIT]->(uni_ctt_roo:CTTermRoot)
        OPTIONAL MATCH (send)-[:HAS_SELECTED_TIMEFRAME]->(tim_fra_val:TimeframeValue)<--(tim_fra_roo:TimeframeRoot)
        CALL {{
                WITH send
                OPTIONAL MATCH (send)-[:HAS_UNIT]->(:UnitDefinitionRoot)-[:LATEST]->(uni_value:UnitDefinitionValue)-[:HAS_CT_UNIT]->(uni_ctt_roo:CTTermRoot)
                OPTIONAL MATCH (send)-[:HAS_CONJUNCTION]->(con:Conjunction)
                WITH distinct send,collect(distinct uni_value.name) as units,
                CASE
                        WHEN con IS NULL THEN ", "
                        ELSE " "+con.string +" "
                end as con_string,
                CASE
                        WHEN uni_value IS NULL THEN ["",""]
                        ELSE [" (",")."]
                end as units_space
                RETURN send as send_uax, units_space[0]+ apoc.text.join([i IN units | toString(i)], con_string) + units_space[1] as unit_str
        }}
        RETURN
        DISTINCT sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
        'TS' AS DOMAIN,
        ectav.code_submission_value AS TSPARMCD,
        ectav.name_submission_value AS TSPARM,
        '' AS controlled_by,
        endp.name_plain + unit_str +' Time frame: ' + tf.name_plain + '.'AS TSVAL,
        '' AS TSVALNF,
        '' AS TSVALCD,
        '' AS TSVCDREF,
        '' AS TSVCDVER
        UNION
        WITH sr, sv
        MATCH (sv)-[:HAS_STUDY_COHORT]->(sch:StudyCohort)
        MATCH (tr:CTTermRoot {{uid:'C126063_NCOHORT'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
        RETURN 
            sv.study_id_prefix+'-'+sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            tav.code_submission_value AS TSPARMCD,
            tav.name_submission_value AS TSPARM,
            '' AS controlled_by,
            count(sch) AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            '' AS TSVCDREF,
            '' AS TSVCDVER
        UNION
        WITH sr, sv
        CALL 
            {{
            WITH sr, sv
            WITH sr as inner_sr, sv as innver_sv
            MATCH (innver_sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(innver_sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(innver_sv),
            (innver_sv) -[:HAS_STUDY_ARM] -(sar:StudyArm)-[:STUDY_ARM_HAS_DESIGN_CELL]-(sd)
            OPTIONAL MATCH (innver_sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            MATCH (tr:CTTermRoot {{uid:'C98771_NARMS'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            RETURN distinct inner_sr,innver_sv, sar,sba, tav
            union all
            WITH sr, sv
            WITH sr as inner_sr, sv as innver_sv
            MATCH (innver_sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement),
            (se)-[:STUDY_ELEMENT_HAS_DESIGN_CELL]-(sd:StudyDesignCell)-[:HAS_STUDY_DESIGN_CELL]-(innver_sv),
            (sd)-[:STUDY_EPOCH_HAS_DESIGN_CELL]-(sep:StudyEpoch)-[:HAS_STUDY_EPOCH]-(innver_sv),
            (innver_sv) -[:HAS_STUDY_BRANCH_ARM]-(sba:StudyBranchArm)-[:STUDY_BRANCH_ARM_HAS_DESIGN_CELL] -(sd),
            (sba)-[:STUDY_ARM_HAS_BRANCH_ARM]-(sar:StudyArm)-[:HAS_STUDY_ARM]-(innver_sv)
            OPTIONAL MATCH (sep) - [:HAS_EPOCH] - (:CTTermRoot) - [:HAS_NAME_ROOT] - (:CTTermNameRoot) -[:LATEST]- (sep_term:CTTermNameValue)
            MATCH (tr:CTTermRoot {{uid:'C98771_NARMS'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            RETURN distinct inner_sr,innver_sv, sar,sba, tav
            }}
        with   tav, inner_sr, innver_sv, count(*) as counter
        return
            innver_sv.study_id_prefix+'-'+innver_sv.study_number AS STUDYID,
            'TS' AS DOMAIN,
            tav.code_submission_value AS TSPARMCD,
            tav.name_submission_value AS TSPARM,
            '' AS controlled_by,
            counter AS TSVAL,
            '' AS TSVALNF,
            '' AS TSVALCD,
            '' AS TSVCDREF,
            '' AS TSVCDVER
        UNION
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound)-[:HAS_TYPE_OF_TREATMENT]->(cttr:CTTermRoot)
            -[:HAS_ATTRIBUTES_ROOT]->(ctar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ctav:CTTermAttributesValue)
            MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(cav:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)-[:LATEST_FINAL]->(cv:CompoundValue)
            -[:HAS_UNII_VALUE]->(uniir:UNIITermRoot)-[:LATEST_FINAL]->(uniiv:UNIITermValue)
            MATCH (uniir)<-[:CONTAINS_DICTIONARY_TERM]-(lib:Library)
            with sv,uniiv,lib,ctav
            MATCH (tr1:CTTermRoot {{uid:'C41161_TRT'}})-->(tar1:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav1:CTTermAttributesValue)
            MATCH (tr2:CTTermRoot {{uid:'C68612_COMPTRT'}})-->(tar2:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav2:CTTermAttributesValue)
            MATCH (tr3:CTTermRoot {{uid:'C85582_CURTRT'}})-->(tar3:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav3:CTTermAttributesValue)
            with tav1,tav2,tav3 , sv, uniiv, lib,
            case ctav.code_submission_value
                WHEN 'INVESTIGATIONAL PRODUCT TYPE OF TREATMENT' THEN
                    tav1 
                WHEN 'COMPARATIVE TREATMENT TYPE OF TREATMENT' THEN
                    tav2 
                WHEN 'CURRENT TREATMENT TYPE OF TREATMENT' THEN
                    tav3 
            end as tav
            RETURN
                sv.study_id_prefix+'-'+sv.study_number as STUDYID,
                'TS' as DOMAIN,
                tav.code_submission_value as TSPARMCD,
                tav.name_submission_value as TSPARM,
                '' AS controlled_by,
                uniiv.name as TSVAL,
                '' AS TSVALNF,
                uniiv.dictionary_id as TSVALCD,
                lib.name as TSVCDREF,
                '' AS TSVCDVER
        UNION 
            WITH sr, sv
            MATCH (ctav:CTTermAttributesValue {{code_submission_value:'INVESTIGATIONAL PRODUCT TYPE OF TREATMENT'}})
            match (sv)-[:HAS_STUDY_COMPOUND]->(sc:StudyCompound)-[:HAS_TYPE_OF_TREATMENT]->(cttr:CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(ctar:CTTermAttributesRoot)-[:LATEST_FINAL]->(ctav)
            match (sc)-[:HAS_SELECTED_COMPOUND]->(cav:CompoundAliasValue)
            match (cav)-[:IS_COMPOUND]->(cr:CompoundRoot)-[:LATEST_FINAL]->(cv:CompoundValue)-[:HAS_UNII_VALUE]->(uniir:UNIITermRoot)-[:LATEST_FINAL]->(uniiv:UNIITermValue)-[:HAS_PCLASS]->(pclass_root:DictionaryTermRoot)-[:LATEST_FINAL]->(medrt:DictionaryTermValue)
            match (pclass_root)<-[:CONTAINS_DICTIONARY_TERM]-(lib:Library)
            match (tr:CTTermRoot {{uid:'C98768_PCLAS'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            RETURN sv.study_id_prefix+'-'+sv.study_number as STUDYID,
                'TS' as DOMAIN,
                tav.code_submission_value as TSPARMCD,
                tav.name_submission_value as TSPARM,
                '' AS controlled_by,
                medrt.name as TSVAL,
                '' AS TSVALNF,
                medrt.dictionary_id as TSVALCD,
                lib.name as TSVCDREF,
                '' AS TSVCDVER
        UNION
            WITH sr, sv
            match (:CTTermRoot{{uid : 'C49488_Y'}})-[:HAS_TYPE]-(sf:StudyField{{ field_name : 'is_trial_randomised'}})-[:HAS_BOOLEAN_FIELD]- (sv)
            match (init_arms:StudyArm)-[:HAS_STUDY_ARM]-(sv)
            with distinct init_arms, sv
            with count( init_arms) as counter_arms,  sum( init_arms.number_of_subjects) as all_num_sub, sv
            where counter_arms>1 
            with all_num_sub, sv
            call{{
                with sv
                match (inv_arms:StudyArm)-[:HAS_STUDY_ARM]-(sv)
                match  (inv_arms)-[:HAS_ARM_TYPE]-(:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST_FINAL]-(:CTTermNameValue{{name:"Investigational Arm"}})
                with collect(distinct inv_arms) as collected_inv_arms
                unwind collected_inv_arms as unwind_inv_arms
                with sum( unwind_inv_arms.number_of_subjects) as inv_num_sub
                return inv_num_sub
            }}
            with all_num_sub, inv_num_sub, sv
            with
            case all_num_sub
                when 0 then 'NA'
                else round(toFloat(inv_num_sub)/all_num_sub,4)
            end as rand_quotient, sv
            match (tr:CTTermRoot {{uid:'C98775_RANDQT'}})-->(tar:CTTermAttributesRoot)-[:LATEST_FINAL]->(tav:CTTermAttributesValue)
            with tav, rand_quotient, sv
            RETURN 
                sv.study_id_prefix+'-'+sv.study_number as STUDYID,
                'TS' as DOMAIN,
                tav.code_submission_value as TSPARMCD,
                tav.name_submission_value as TSPARM,
                '' AS controlled_by,
                rand_quotient as TSVAL,
                '' AS TSVALNF,
                '' as TSVALCD,
                '' as TSVCDREF,
                '' AS TSVCDVER
        }}
        RETURN *
        ORDER BY TSPARMCD
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )

        return utils.db_result_to_list(result_array)

    def get_te(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        MATCH (sv)-[:HAS_STUDY_ELEMENT]->(se:StudyElement)
        RETURN 
            toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TE' AS DOMAIN,
            se.uid,
            se.order AS ETCD,
            se.name AS ELEMENT,
            se.start_rule AS TESTRL,
            se.end_rule AS TEENRL,
            se.planned_duration AS TEDUR
            ORDER BY se.order
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )
        return utils.db_result_to_list(result_array)

    def get_tdm(
        self,
        study_uid,
        study_value_version: str | None = None,
    ) -> list[Any]:
        if study_value_version:
            query = MATCH_SPECIFIC_STUDY_VERSION
        else:
            query = MATCH_LATEST_STUDY
        query = (
            query
            + """
        MATCH (sv)-[:HAS_STUDY_DISEASE_MILESTONE]->(sdm:StudyDiseaseMilestone)
        MATCH (sdm)-[:HAS_DISEASE_MILESTONE_TYPE]-(tr:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST]-(sdm_term:CTTermNameValue)
        MATCH (tr)-[HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[LATEST]->(ctav:CTTermAttributesValue)
        RETURN DISTINCT toUpper(sv.study_id_prefix + '-' + sv.study_number) AS STUDYID,
            'TM' AS DOMAIN,
            sdm_term.name AS MIDSTYPE ,
            ctav.definition AS TMDEF,
            case sdm.repetition_indicator
                when true then 'Y'
                when false then 'N'
            END AS TMRPT
        """
        )
        result_array = db.cypher_query(
            query=query,
            params={
                "study_uid": str(study_uid),
                "study_value_version": str(study_value_version),
            },
        )
        return utils.db_result_to_list(result_array)
