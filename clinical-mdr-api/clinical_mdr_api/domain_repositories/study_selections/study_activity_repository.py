import datetime
from dataclasses import dataclass
from typing import Any

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityRoot,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivityGroup,
    StudyActivitySubGroup,
    StudySelection,
    StudySoAGroup,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityAR,
    StudySelectionActivityVO,
)
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_activity_subgroup_uid: str
    study_activity_subgroup_order: int | None
    activity_subgroup_uid: str
    study_activity_group_uid: str
    study_activity_group_order: int | None
    activity_group_uid: str
    activity_uid: str
    soa_group_term_uid: str
    study_soa_group_uid: str
    study_soa_group_order: int | None
    author_id: str
    change_type: str
    start_date: datetime.datetime
    show_activity_group_in_protocol_flowchart: bool | None
    show_activity_subgroup_in_protocol_flowchart: bool | None
    show_activity_in_protocol_flowchart: bool | None
    show_soa_group_in_protocol_flowchart: bool | None
    order: int | None
    end_date: datetime.datetime | None
    activity_version: str | None


class StudySelectionActivityRepository(
    StudySelectionActivityBaseRepository[StudySelectionActivityAR]
):
    _aggregate_root_type = StudySelectionActivityAR

    def _create_value_object_from_repository(
        self, selection: dict[Any, Any], acv: bool
    ) -> StudySelectionActivityVO:
        study_activity_subgroup = selection.get("study_activity_subgroup") or {}
        study_activity_group = selection.get("study_activity_group") or {}
        study_soa_group = selection.get("study_soa_group") or {}
        return StudySelectionActivityVO.from_input_values(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_subgroup_uid=study_activity_subgroup.get("selection_uid"),
            study_activity_subgroup_order=study_activity_subgroup.get("order"),
            activity_subgroup_uid=study_activity_subgroup.get("activity_subgroup_uid"),
            activity_subgroup_name=study_activity_subgroup.get(
                "activity_subgroup_name"
            ),
            study_activity_group_uid=study_activity_group.get("selection_uid"),
            study_activity_group_order=study_activity_group.get("order"),
            activity_group_uid=study_activity_group.get("activity_group_uid"),
            activity_group_name=study_activity_group.get("activity_group_name"),
            study_uid=selection["study_uid"],
            activity_uid=selection["activity_uid"],
            activity_name=selection["activity_name"],
            activity_version=selection["activity_version"],
            activity_library_name=selection["activity_library_name"],
            soa_group_term_uid=study_soa_group.get("soa_group_term_uid"),
            soa_group_term_name=study_soa_group.get("soa_group_term_name"),
            study_soa_group_uid=study_soa_group.get("selection_uid"),
            study_soa_group_order=study_soa_group.get("order"),
            order=selection["order"],
            show_activity_in_protocol_flowchart=selection[
                "show_activity_in_protocol_flowchart"
            ],
            show_activity_group_in_protocol_flowchart=study_activity_group.get(
                "show_activity_group_in_protocol_flowchart"
            ),
            show_activity_subgroup_in_protocol_flowchart=study_activity_subgroup.get(
                "show_activity_subgroup_in_protocol_flowchart"
            ),
            show_soa_group_in_protocol_flowchart=study_soa_group.get(
                "show_soa_group_in_protocol_flowchart"
            ),
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
            author_username=selection["author_username"],
            accepted_version=acv,
            keep_old_version=selection.get("keep_old_version"),
        )

    def _additional_match(self) -> str:
        return """
            WITH sr, sv
            
            CALL {
                WITH sr, sv 
                OPTIONAL MATCH (sv)-[:HAS_STUDY_STANDARD_VERSION]->(study_standard_version:StudyStandardVersion)<-[:AFTER]-(:StudyAction)<-[:AUDIT_TRAIL]-(sr)
                OPTIONAL MATCH (study_standard_version)-[:HAS_CT_PACKAGE]->(ct_package:CTPackage)
                WHERE ct_package.uid CONTAINS "SDTM CT"
                RETURN datetime(ct_package.effective_date + 'T23:59:59.999999000Z') AS terms_at_specific_datetime
            }
            
            MATCH (sv)-[:HAS_STUDY_ACTIVITY]->(sa:StudyActivity)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)<-[ver:HAS_VERSION]-(ar:ActivityRoot)<-[:CONTAINS_CONCEPT]-(lib:Library)
            
            WITH DISTINCT *
            
            CALL {
                WITH sa, terms_at_specific_datetime
                MATCH (sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(soa_group_term_root:CTTermRoot)
                MATCH (soa_group)<-[:AFTER]-(after_action:StudyAction)
                WITH *
                ORDER BY after_action.date DESC
                LIMIT 1
            
                WITH soa_group_term_root, terms_at_specific_datetime, soa_group
                MATCH (:Library)-[:CONTAINS_TERM]->(soa_group_term_root)-[:HAS_NAME_ROOT]->(term_name_root:CTTermNameRoot)-[term_version:HAS_VERSION]->(term_name_value:CTTermNameValue)
                WHERE term_version.status IN ['Final', 'Retired'] AND ( terms_at_specific_datetime IS NULL
                      OR term_version.start_date <= datetime(terms_at_specific_datetime)
                      AND (term_version.end_date IS NULL OR term_version.end_date > datetime(terms_at_specific_datetime)) )
                RETURN {uid: soa_group_term_root.uid, name: term_name_value.name} AS soa_group_term, soa_group
                ORDER BY term_version.start_date DESC
                LIMIT 1
            }
        """

    def _filter_clause(self, query_parameters: dict[Any, Any], **kwargs) -> str:
        # Filter on Activity, ActivityGroup or ActivityGroupNames if provided as a specific filter
        # This improves performance vs full service level filter
        activity_names = kwargs.get("activity_names")
        activity_group_names = kwargs.get("activity_group_names")
        activity_subgroup_names = kwargs.get("activity_subgroup_names")
        study_activity_subgroup_uid = kwargs.get("study_activity_subgroup_uid")
        study_soa_group_uid = kwargs.get("study_soa_group_uid")
        find_requested_study_activities = kwargs.get("find_requested_study_activities")
        filter_query = ""
        if (
            activity_names is not None
            or activity_group_names is not None
            or activity_subgroup_names is not None
            or study_activity_subgroup_uid is not None
            or study_soa_group_uid is not None
        ):
            filter_query += "\nWITH *\nWHERE\n"
            filter_list = []
            if activity_names is not None:
                filter_list.append("av.name IN $activity_names")
                query_parameters["activity_names"] = activity_names
            if activity_subgroup_names is not None:
                filter_list.append(
                    "size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sas:StudyActivitySubGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)"
                    " WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
                )
                query_parameters["activity_subgroup_names"] = activity_subgroup_names
            if activity_group_names is not None:
                filter_list.append(
                    "size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sas:StudyActivityGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)"
                    " WHERE activity_group_value.name IN $activity_group_names | activity_group_value.name]) > 0"
                )
                query_parameters["activity_group_names"] = activity_group_names
            if study_activity_subgroup_uid is not None:
                filter_list.append(
                    """size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sas:StudyActivitySubGroup)
                            WHERE sas.uid=$study_activity_subgroup_uid | sas.uid]) > 0"""
                )
                query_parameters["study_activity_subgroup_uid"] = (
                    study_activity_subgroup_uid
                )
            if (
                find_requested_study_activities is not None
                and study_soa_group_uid is not None
                and study_activity_subgroup_uid is None
            ):
                filter_list.append(
                    """size([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)
                            WHERE lib.name='Requested' AND soa_group.uid=$study_soa_group_uid AND NOT (sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->() | soa_group.uid]) > 0"""
                )
                query_parameters["study_soa_group_uid"] = study_soa_group_uid
            filter_query += " AND ".join(filter_list)
        return filter_query

    def _return_clause(self) -> str:
        return """
                RETURN DISTINCT
                sr.uid AS study_uid,
                sa.order AS order,
                sa.uid AS study_selection_uid,
                sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                {
                    selection_uid: soa_group.uid, 
                    soa_group_term_uid: soa_group_term.uid,
                    soa_group_term_name: soa_group_term.name,
                    show_soa_group_in_protocol_flowchart: coalesce(soa_group.show_soa_group_in_protocol_flowchart, false),
                    order: soa_group.order
                } AS study_soa_group,
               head(apoc.coll.sortMulti([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection:StudyActivitySubGroup)
                -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) |
                    {
                        selection_uid: study_activity_subgroup_selection.uid, 
                        activity_subgroup_uid:activity_subgroup_root.uid,
                        activity_subgroup_name:activity_subgroup_value.name,
                        show_activity_subgroup_in_protocol_flowchart:study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart,
                        order: study_activity_subgroup_selection.order,
                        date: head([(study_activity_subgroup_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                    }], ['date'])) AS study_activity_subgroup,
                head(apoc.coll.sortMulti([(sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection:StudyActivityGroup)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                    {
                        selection_uid: study_activity_group_selection.uid, 
                        activity_group_uid: activity_group_root.uid,
                        activity_group_name: activity_group_value.name,
                        show_activity_group_in_protocol_flowchart: study_activity_group_selection.show_activity_group_in_protocol_flowchart,
                        order: study_activity_group_selection.order,
                        date: head([(study_activity_group_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                    }], ['date'])) AS study_activity_group,
                sa.accepted_version AS accepted_version,
                ar.uid AS activity_uid,
                av.name AS activity_name,
                sac.date AS start_date,
                sac.author_id AS author_id,
                COALESCE(head([(user:User)-[*0]-() WHERE user.user_id=sac.author_id | user.username]), sac.author_id) AS author_username,
                hv_ver.version AS activity_version,
                lib.name as activity_library_name,
                coalesce(sa.keep_old_version, false) AS keep_old_version
            """

    def get_selection_history(
        self, selection: dict[Any, Any], change_type: str, end_date: datetime.datetime
    ):
        study_activity_subgroup = selection.get("study_activity_subgroup") or {}
        study_activity_group = selection.get("study_activity_group") or {}
        study_soa_group = selection.get("study_soa_group") or {}
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_subgroup_uid=study_activity_subgroup.get("selection_uid"),
            study_activity_subgroup_order=study_activity_subgroup.get("order"),
            activity_subgroup_uid=study_activity_subgroup.get("activity_subgroup_uid"),
            study_activity_group_uid=study_activity_group.get("selection_uid"),
            study_activity_group_order=study_activity_group.get("order"),
            activity_group_uid=study_activity_group.get("activity_group_uid"),
            activity_uid=selection["activity_uid"],
            order=selection["order"],
            activity_version=selection["activity_version"],
            soa_group_term_uid=study_soa_group.get("soa_group_term_uid"),
            study_soa_group_uid=study_soa_group.get("selection_uid"),
            study_soa_group_order=study_soa_group.get("order"),
            author_id=selection["author_id"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            show_activity_in_protocol_flowchart=selection[
                "show_activity_in_protocol_flowchart"
            ],
            show_activity_group_in_protocol_flowchart=study_activity_group.get(
                "show_activity_group_in_protocol_flowchart"
            ),
            show_activity_subgroup_in_protocol_flowchart=study_activity_subgroup.get(
                "show_activity_subgroup_in_protocol_flowchart"
            ),
            show_soa_group_in_protocol_flowchart=study_soa_group.get(
                "show_soa_group_in_protocol_flowchart"
            ),
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivity { uid: $study_selection_uid})
            WITH sa
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivity)
            WITH distinct(all_sa)
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivity)
            WITH DISTINCT all_sa
            """
        audit_trail_cypher += """
                    MATCH (all_sa)-[:HAS_SELECTED_ACTIVITY]->(av:ActivityValue)

                    CALL {
                      WITH av
                      MATCH (av) <-[ver]-(ar:ActivityRoot)
                      WHERE ver.status = "Final"
                      RETURN ver as ver, ar as ar
                      ORDER BY ver.start_date DESC
                      LIMIT 1
                    }
                    WITH DISTINCT all_sa, ar, ver
                    ORDER BY all_sa.order ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, ar, asa, bsa, ver
                    ORDER BY all_sa.uid, asa.date DESC
                    RETURN
                        all_sa.order AS order,
                        all_sa.uid AS study_selection_uid,
                        all_sa.show_activity_in_protocol_flowchart AS show_activity_in_protocol_flowchart,
                        head(apoc.coll.sortMulti([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(soa_group:StudySoAGroup)-[:HAS_FLOWCHART_GROUP]->(soa_group_term_root:CTTermRoot) | 
                        {
                            selection_uid: soa_group.uid, 
                            soa_group_term_uid: soa_group_term_root.uid,
                            show_soa_group_in_protocol_flowchart: coalesce(soa_group.show_soa_group_in_protocol_flowchart, false),
                            order: soa_group.order,
                            date: head([(soa_group)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                        }], ['date'])) AS study_soa_group,
                        head(apoc.coll.sortMulti([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection:StudyActivitySubGroup)
                            -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | 
                            {
                                selection_uid: study_activity_subgroup_selection.uid, 
                                activity_subgroup_uid:activity_subgroup_root.uid,
                                show_activity_subgroup_in_protocol_flowchart:study_activity_subgroup_selection.show_activity_subgroup_in_protocol_flowchart,
                                order: study_activity_subgroup_selection.order,
                                date: head([(study_activity_subgroup_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                            }], ['date'])) AS study_activity_subgroup,
                        head(apoc.coll.sortMulti([(all_sa)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection:StudyActivityGroup)
                            -[:HAS_SELECTED_ACTIVITY_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                            {
                                selection_uid: study_activity_group_selection.uid, 
                                activity_group_uid: activity_group_root.uid,
                                show_activity_group_in_protocol_flowchart:study_activity_group_selection.show_activity_group_in_protocol_flowchart,
                                order: study_activity_group_selection.order,
                                date: head([(study_activity_group_selection)<-[:AFTER]-(after_action:StudyAction) | after_action.date])
                            }], ['date'])) AS study_activity_group,
                        ar.uid AS activity_uid,
                        asa.date AS start_date,
                        asa.author_id AS author_id,
                        labels(asa) AS change_type,
                        bsa.date AS end_date,
                        ver.version AS activity_version
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return study_value.has_study_activity.get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivityVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyActivity,
        for_deletion: bool = False,
    ):
        # find the activity value
        activity_root_node: ActivityRoot = ActivityRoot.nodes.get(
            uid=selection.activity_uid
        )
        latest_activity_value_node: ActivityValue = (
            activity_root_node.get_value_for_version(selection.activity_version)
        )
        # Create new activity selection
        study_activity_selection_node = StudyActivity(
            order=order,
            show_activity_in_protocol_flowchart=selection.show_activity_in_protocol_flowchart,
            keep_old_version=selection.keep_old_version,
        )
        study_activity_selection_node.uid = selection.study_selection_uid
        study_activity_selection_node.accepted_version = selection.accepted_version
        study_activity_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_activity.connect(
                study_activity_selection_node
            )
        # Connect new node with audit trail
        audit_node.has_after.connect(study_activity_selection_node)
        # Connect new node with Activity value
        study_activity_selection_node.has_selected_activity.connect(
            latest_activity_value_node
        )
        # Connect StudyActivity with StudySoAGroup node
        study_soa_group_node = StudySoAGroup.nodes.has(has_before=False).get(
            uid=selection.study_soa_group_uid
        )
        study_activity_selection_node.has_soa_group_selection.connect(
            study_soa_group_node
        )

        if selection.study_activity_subgroup_uid:
            # Connect StudyActivity with StudyActivitySubGroup node
            study_activity_subgroup = StudyActivitySubGroup.nodes.has(
                has_before=False
            ).get(uid=selection.study_activity_subgroup_uid)
            study_activity_selection_node.study_activity_has_study_activity_subgroup.connect(
                study_activity_subgroup
            )

        if selection.study_activity_group_uid:
            # Connect StudyActivity with StudyActivityGroup node
            study_activity_group = StudyActivityGroup.nodes.has(has_before=False).get(
                uid=selection.study_activity_group_uid
            )
            study_activity_selection_node.study_activity_has_study_activity_group.connect(
                study_activity_group
            )
        if last_study_selection_node:
            manage_previous_connected_study_selection_relationships(
                previous_item=last_study_selection_node,
                study_value_node=latest_study_value_node,
                new_item=study_activity_selection_node,
                exclude_study_selection_relationships=[
                    StudySoAGroup,
                    StudyActivitySubGroup,
                    StudyActivityGroup,
                ],
            )

    def generate_uid(self) -> str:
        return StudyActivity.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass
