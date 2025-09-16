from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityGroupValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity_group import (
    ActivityGroupAR,
    ActivityGroupVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from common.exceptions import BusinessLogicException
from common.utils import convert_to_datetime


class ActivityGroupRepository(ConceptGenericRepository[ActivityGroupAR]):
    root_class = ActivityGroupRoot
    value_class = ActivityGroupValue
    return_model = ActivityGroup

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivityGroupAR:
        major, minor = input_dict["version"].split(".")
        return ActivityGroupAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=ActivityGroupVO.from_repository_values(
                name=input_dict["name"],
                name_sentence_case=input_dict.get("name_sentence_case"),
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=convert_to_datetime(value=input_dict.get("end_date")),
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_ar(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityGroupAR:
        return ActivityGroupAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityGroupVO.from_repository_values(
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                definition=value.definition,
                abbreviation=value.abbreviation,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityGroupAR:
        return self._create_ar(
            root=root, library=library, relationship=relationship, value=value
        )

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = """
            size([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:HAS_GROUP]-(v:ActivitySubGroupValue) 
            WHERE v.name IN $activity_subgroup_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = """
            size([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:IN_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(v:ActivityValue) 
            WHERE v.name IN $activity_names | v.name]) > 0"""
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        extended_filter_statements = " AND ".join(filter_parameters)
        if filter_statements_from_concept != "":
            if len(extended_filter_statements) > 0:
                filter_statements_to_return = " AND ".join(
                    [filter_statements_from_concept, extended_filter_statements]
                )
            else:
                filter_statements_to_return = filter_statements_from_concept
        else:
            filter_statements_to_return = (
                "WHERE " + extended_filter_statements
                if len(extended_filter_statements) > 0
                else ""
            )
        return filter_statements_to_return, filter_query_parameters

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the activity_generic_repository_impl
        return """
        WITH *,
            head([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:HAS_GROUP]-(activity_sub_group_value:ActivitySubGroupValue)<-[:HAS_VERSION]-
            (activity_sub_group_root:ActivitySubGroupRoot) | {uid:activity_sub_group_root.uid, name:activity_sub_group_value.name}]) AS activity_subgroup,
            head([(concept_value)<-[:IN_GROUP]-(:ActivityValidGroup)<-[:IN_SUBGROUP]-(:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)
            <-[:HAS_VERSION]-(activity_root:ActivityRoot) | {uid:activity_root.uid, name:activity_value.name}]) AS activity
        """

    def _create_new_value_node(self, ar: ActivityGroupAR) -> ActivityGroupValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()
        return value_node

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityGroupRoot)-[version:HAS_VERSION]->(concept_value:ActivityGroupValue)
        """

    def get_cosmos_group_overview(self, group_uid: str) -> dict[str, Any]:
        """
        Get a COSMoS compatible representation of a specific activity group.
        Similar to get_group_overview but formatted for COSMoS.

        Args:
            group_uid: The UID of the activity group

        Returns:
            A dictionary representation compatible with COSMoS format
        """

        query = """
        MATCH (group_root:ActivityGroupRoot {uid:$uid})-[:LATEST]->(group_value:ActivityGroupValue)
        WITH DISTINCT group_root, group_value,
            head([(library)-[:CONTAINS_CONCEPT]->(group_root) | library.name]) AS group_library_name,
            [(group_root)-[versions:HAS_VERSION]->(:ActivityGroupValue) | versions.version] as all_versions,
            apoc.coll.toSet([(sgv:ActivitySubGroupValue)-[:HAS_GROUP]->(avg:ActivityValidGroup)-[:IN_GROUP]->(group_value)
                | {
                    uid: head([(sgr:ActivitySubGroupRoot)-[:HAS_VERSION]->(sgv) | sgr.uid]),
                    name: sgv.name,
                    definition: sgv.definition,
                    status: head([(sgr:ActivitySubGroupRoot)-[hv:HAS_VERSION]->(sgv) | hv.status]),
                    version: head([(sgr:ActivitySubGroupRoot)-[hv:HAS_VERSION]->(sgv) | hv.version])
                }]) AS linked_subgroups,
            apoc.coll.toSet(
                [(group_value)<-[:IN_GROUP]-(activity_valid_group:ActivityValidGroup)<-[:IN_SUBGROUP]-
                (activity_grouping:ActivityGrouping)<-[:HAS_GROUPING]-(activity_value:ActivityValue)<-[:HAS_VERSION]-
                (activity_root:ActivityRoot)
                WHERE NOT EXISTS ((activity_value)<--(:DeletedActivityRoot))
                | {
                    uid: activity_root.uid,
                    name: activity_value.name,
                    definition: activity_value.definition,
                    nci_concept_id: activity_value.nci_concept_id,
                    status: head([(activity_root)-[hv:HAS_VERSION]->(activity_value) | hv.status]),
                    version: head([(activity_root)-[hv:HAS_VERSION]->(activity_value) | hv.version])
                }]) AS linked_activities
        RETURN
            {
                uid: group_root.uid,
                name: group_value.name,
                name_sentence_case: group_value.name_sentence_case,
                definition: group_value.definition,
                abbreviation: group_value.abbreviation
            } AS group_value,
            group_library_name,
            linked_subgroups,
            linked_activities,
            apoc.coll.dropDuplicateNeighbors(
                [v in apoc.coll.sortMulti(
                    [v in all_versions | {
                        version: v,
                        major: toInteger(split(v, '.')[0]),
                        minor: toInteger(split(v, '.')[1])
                    }],
                    ['major', 'minor']
                ) | v.version]
            ) AS all_versions
        """

        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": group_uid}
        )
        BusinessLogicException.raise_if(
            len(result_array) != 1,
            msg=f"The overview query returned broken data: {result_array}",
        )

        overview = result_array[0]
        overview_dict = {}
        for overview_prop, attribute_name in zip(overview, attribute_names):
            overview_dict[attribute_name] = overview_prop

        return overview_dict

    def get_linked_activity_subgroup_uids(
        self,
        group_uid: str,
        version: str,
        skip: int = 0,
        limit: int | None = None,
        count_total: bool = False,
    ) -> dict[str, Any]:
        """
        Get the UIDs of all activity subgroups linked to a specific activity group version.
        Will return the latest version of each subgroup connected to this activity group version.

        Args:
            group_uid: The UID of the activity group
            version: The version of the activity group
            skip: Number of records to skip (for pagination)
            limit: Maximum number of records to return (for pagination)
            count_total: Whether to count the total number of records

        Returns:
            A dictionary containing the subgroups list and optionally the total count
        """
        query = """
        // 1. Find a specific activity group version - use LIMIT 1 to handle duplicates
        MATCH (gr:ActivityGroupRoot {uid: $group_uid})-[gv_rel:HAS_VERSION {version: $version}]->(gv:ActivityGroupValue)
        WITH gr, gv, gv_rel
        ORDER BY gv_rel.start_date DESC
        LIMIT 1

        // 2. Find when this version's validity ends (either its end_date or the start of the next version)
        OPTIONAL MATCH (gr)-[next_rel:HAS_VERSION]->(next_gv:ActivityGroupValue)
        WHERE toFloat(next_rel.version) > toFloat(gv_rel.version)
        WITH gv, gr, gv_rel, 
             CASE WHEN gv_rel.end_date IS NULL 
                  THEN min(next_rel.start_date) 
                  ELSE gv_rel.end_date 
             END as version_end_date

        // 3. Find all subgroups linked to this group version through ActivityValidGroup
        MATCH (avg:ActivityValidGroup)-[:IN_GROUP]->(gv)
        MATCH (sgv:ActivitySubGroupValue)-[:HAS_GROUP]->(avg)
        MATCH (sgr:ActivitySubGroupRoot)-[sgv_rel:HAS_VERSION]->(sgv)

        // 4. Filter subgroup versions that existed when this activity group version was active
        WITH gr, gv, gv_rel, version_end_date, sgr, sgv, sgv_rel
        WHERE sgv_rel.start_date <= COALESCE(version_end_date, datetime())
        
        // 5. Group by subgroup to get all valid versions
        WITH DISTINCT sgr.uid as subgroup_uid,
             collect(DISTINCT {
                 version: sgv_rel.version,
                 name: sgv.name,
                 definition: sgv.definition,
                 status: sgv_rel.status,
                 major: toInteger(SPLIT(sgv_rel.version, '.')[0]),
                 minor: toInteger(SPLIT(sgv_rel.version, '.')[1]),
                 start_date: sgv_rel.start_date
             }) as versions

        // 6. Find the highest version of each subgroup that existed before the activity group's end
        WITH subgroup_uid, versions,
             reduce(highest = versions[0], v IN versions | 
                 CASE 
                     WHEN v.major > highest.major THEN v
                     WHEN v.major = highest.major AND v.minor > highest.minor THEN v
                     ELSE highest
                 END
             ) as latest_version
        WHERE latest_version IS NOT NULL

        // 7. Return the appropriate version of each subgroup
        RETURN {
            uid: subgroup_uid,
            name: latest_version.name,
            version: latest_version.version,
            status: latest_version.status,
            definition: latest_version.definition
        } as result
        """

        # Add pagination if needed
        if limit is not None:
            query += " SKIP $skip LIMIT $limit"

        # Prepare parameters
        params: dict[str, str | int] = {
            "group_uid": group_uid,
            "version": version,
        }

        if limit is not None:
            params["skip"] = skip
            params["limit"] = limit

        # Execute query to get paginated subgroups
        results, _ = db.cypher_query(query, params)

        # Get total count if requested
        total = None
        if count_total:
            count_query = """
            // Count distinct subgroups with temporal filtering
            MATCH (gr:ActivityGroupRoot {uid: $group_uid})-[gv_rel:HAS_VERSION {version: $version}]->(gv:ActivityGroupValue)
            WITH gr, gv, gv_rel
            ORDER BY gv_rel.start_date DESC
            LIMIT 1
            
            // Find when this version's validity ends
            OPTIONAL MATCH (gr)-[next_rel:HAS_VERSION]->(next_gv:ActivityGroupValue)
            WHERE toFloat(next_rel.version) > toFloat(gv_rel.version)
            WITH gv, gr, gv_rel, 
                 CASE WHEN gv_rel.end_date IS NULL 
                      THEN min(next_rel.start_date) 
                      ELSE gv_rel.end_date 
                 END as version_end_date
                 
            MATCH (avg:ActivityValidGroup)-[:IN_GROUP]->(gv)
            MATCH (sgv:ActivitySubGroupValue)-[:HAS_GROUP]->(avg)
            MATCH (sgr:ActivitySubGroupRoot)-[sgv_rel:HAS_VERSION]->(sgv)
            WHERE sgv_rel.start_date <= COALESCE(version_end_date, datetime())
            RETURN count(DISTINCT sgr.uid) as total
            """
            count_result, _ = db.cypher_query(
                count_query, {"group_uid": group_uid, "version": version}
            )
            total = count_result[0][0] if count_result else 0

        # Return results
        subgroups = [dict(result[0]) for result in results] if results else []

        return {"subgroups": subgroups, "total": total}
