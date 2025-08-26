import datetime
from dataclasses import dataclass
from typing import Any

from clinical_mdr_api.domain_repositories.generic_repository import (
    manage_previous_connected_study_selection_relationships,
)
from clinical_mdr_api.domain_repositories.models._utils import ListDistinct
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityInstanceRoot,
    ActivityInstanceValue,
)
from clinical_mdr_api.domain_repositories.models.study import StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudyActivity,
    StudyActivityInstance,
    StudySelection,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_base_repository import (
    StudySelectionActivityBaseRepository,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceAR,
    StudySelectionActivityInstanceVO,
)
from common.utils import convert_to_datetime


@dataclass
class SelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    study_activity_uid: str
    activity_uid: str
    activity_version: str
    activity_instance_uid: str | None
    activity_instance_name: str | None
    activity_instance_version: str | None
    show_activity_instance_in_protocol_flowchart: bool
    author_id: str
    change_type: str
    start_date: datetime.datetime
    end_date: datetime.datetime | None


class StudySelectionActivityInstanceRepository(
    StudySelectionActivityBaseRepository[StudySelectionActivityInstanceAR]
):
    _aggregate_root_type = StudySelectionActivityInstanceAR

    def is_repository_based_on_ordered_selection(self):
        return False

    def _create_value_object_from_repository(
        self, selection: dict[Any, Any], acv: bool
    ) -> StudySelectionActivityInstanceVO:
        activity = selection.get("activity") or {}
        activity_instance = selection.get("activity_instance") or {}
        study_activity_subgroup = selection.get("study_activity_subgroup") or {}
        study_activity_group = selection.get("study_activity_group") or {}
        study_soa_group = selection.get("study_soa_group") or {}
        return StudySelectionActivityInstanceVO.from_input_values(
            study_uid=selection["study_uid"],
            study_selection_uid=selection["study_selection_uid"],
            study_activity_uid=selection["study_activity_uid"],
            activity_uid=activity.get("uid"),
            activity_name=activity.get("name"),
            activity_version=f"{activity.get('major_version')}.{activity.get('minor_version')}",
            activity_instance_uid=activity_instance.get("uid"),
            activity_instance_name=activity_instance.get("name"),
            activity_instance_version=(
                f"{activity_instance.get('major_version')}.{activity_instance.get('minor_version')}"
                if activity_instance
                else None
            ),
            show_activity_instance_in_protocol_flowchart=selection[
                "show_activity_instance_in_protocol_flowchart"
            ],
            keep_old_version=selection["keep_old_version"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
            author_username=selection["author_username"],
            accepted_version=acv,
            study_activity_subgroup_uid=study_activity_subgroup.get("selection_uid"),
            activity_subgroup_uid=study_activity_subgroup.get("activity_subgroup_uid"),
            activity_subgroup_name=study_activity_subgroup.get(
                "activity_subgroup_name"
            ),
            study_activity_group_uid=study_activity_group.get("selection_uid"),
            activity_group_uid=study_activity_group.get("activity_group_uid"),
            activity_group_name=study_activity_group.get("activity_group_name"),
            study_soa_group_uid=study_soa_group.get("selection_uid"),
            soa_group_term_uid=study_soa_group.get("soa_group_uid"),
            soa_group_term_name=study_soa_group.get("soa_group_name"),
        )

    def _order_by_query(self):
        return """
            WITH DISTINCT *
            MATCH (sa)<-[:AFTER]-(sac:StudyAction)
        """

    def _versioning_query(self) -> str:
        return ""

    def _additional_match(self) -> str:
        return """
            WITH sr, sv
            MATCH (sv)-[:HAS_STUDY_ACTIVITY_INSTANCE]->(sa:StudyActivityInstance)
                <-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]-(study_activity:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(sv)
        """

    def _filter_clause(self, query_parameters: dict[Any, Any], **kwargs) -> str:
        # Filter on Activity, ActivityGroup or ActivityGroupNames if provided as a specific filter
        # This improves performance vs full service level filter
        activity_names = kwargs.get("activity_names")
        activity_group_names = kwargs.get("activity_group_names")
        activity_subgroup_names = kwargs.get("activity_subgroup_names")
        activity_instance_names = kwargs.get("activity_instance_names")
        filter_query = ""
        if (
            activity_names is not None
            or activity_group_names is not None
            or activity_subgroup_names is not None
            or activity_instance_names is not None
        ):
            filter_query += " WHERE "
            filter_list = []
            if activity_names is not None:
                filter_list.append(
                    "head([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue) | activity_value.name]) IN $activity_names"
                )
                query_parameters["activity_names"] = activity_names
            if activity_subgroup_names is not None:
                filter_list.append(
                    "size([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(sas:StudyActivitySubGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)"
                    "WHERE activity_subgroup_value.name IN $activity_subgroup_names | activity_subgroup_value.name]) > 0"
                )
                query_parameters["activity_subgroup_names"] = activity_subgroup_names
            if activity_group_names is not None:
                filter_list.append(
                    "size([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(sas:StudyActivityGroup)-"
                    "[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)"
                    "WHERE activity_group_value.name IN $activity_group_names | activity_group_value.name]) > 0"
                )
                query_parameters["activity_group_names"] = activity_group_names
            if activity_instance_names is not None:
                filter_list.append(
                    "size([(sa)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue)"
                    "WHERE activity_instance_value.name IN $activity_instance_names | activity_instance_value.name]) > 0"
                )
                query_parameters["activity_instance_names"] = activity_instance_names
            filter_query += " AND ".join(filter_list)
        return filter_query

    def _return_clause(self) -> str:
        return """RETURN DISTINCT
                sr.uid AS study_uid,
                sa.uid AS study_selection_uid,
                coalesce(sa.show_activity_instance_in_protocol_flowchart, false) AS show_activity_instance_in_protocol_flowchart,
                coalesce(sa.keep_old_version, false) AS keep_old_version,
                study_activity.uid AS study_activity_uid,
                head(apoc.coll.sortMulti([(study_activity)-[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[has_version:HAS_VERSION]
                -(activity_root:ActivityRoot) WHERE has_version.status IN ['Final', 'Retired'] | 
                    {
                        uid: activity_root.uid,
                        name: activity_value.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        order: study_activity.order
                    }], ['major_version', 'minor_version'])) AS activity,
                head(apoc.coll.sortMulti([(sa)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_name:ActivityInstanceValue)<-[has_version:HAS_VERSION]
                -(activity_instance_root:ActivityInstanceRoot) WHERE has_version.status IN ['Final', 'Retired'] |  
                    { 
                        uid: activity_instance_root.uid, 
                        name:activity_instance_name.name,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        order: sa.order
                    }], ['major_version', 'minor_version'])) AS activity_instance,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_SUBGROUP]->(study_activity_subgroup_selection)
                    -[:HAS_SELECTED_ACTIVITY_SUBGROUP]->(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | 
                    {
                        selection_uid: study_activity_subgroup_selection.uid, 
                        activity_subgroup_uid:activity_subgroup_root.uid,
                        activity_subgroup_name: activity_subgroup_value.name,
                        order: study_activity_subgroup_selection.order
                    }]) AS study_activity_subgroup,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_GROUP]->(study_activity_group_selection)
                    -[:HAS_SELECTED_ACTIVITY_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | 
                    {
                        selection_uid: study_activity_group_selection.uid, 
                        activity_group_uid: activity_group_root.uid,
                        activity_group_name: activity_group_value.name,
                        order: study_activity_group_selection.order
                    }]) AS study_activity_group,
                head([(study_activity)-[:STUDY_ACTIVITY_HAS_STUDY_SOA_GROUP]->(study_soa_group_selection)
                    -[:HAS_FLOWCHART_GROUP]->(ct_term_root:CTTermRoot)-[:HAS_NAME_ROOT]-(:CTTermNameRoot)-[:LATEST]->(flowchart_value:CTTermNameValue) | 
                    {
                        selection_uid: study_soa_group_selection.uid, 
                        soa_group_uid: ct_term_root.uid,
                        soa_group_name: flowchart_value.name,
                        order: study_soa_group_selection.order
                    }]) AS study_soa_group,
                sac.date AS start_date,
                sac.author_id AS author_id,
                COALESCE(head([(user:User)-[*0]-() WHERE user.user_id=sac.author_id | user.username]), sac.author_id) AS author_username
                ORDER BY study_soa_group.order, study_activity_group.order, study_activity_subgroup.order, activity.order, activity_instance.order
        """

    def get_selection_history(
        self, selection: dict[Any, Any], change_type: str, end_date: datetime.datetime
    ):
        study_activity = selection.get("study_activity", {})
        activity_instance = selection.get("activity_instance", {})
        return SelectionHistory(
            study_selection_uid=selection["study_selection_uid"],
            study_activity_uid=study_activity.get("uid"),
            activity_uid=study_activity.get("activity_uid"),
            activity_version=f"{study_activity.get('major_version')}.{study_activity.get('minor_version')}",
            activity_instance_uid=(
                activity_instance.get("uid") if activity_instance else None
            ),
            activity_instance_name=(
                activity_instance.get("name") if activity_instance else None
            ),
            activity_instance_version=(
                f"{activity_instance.get('major_version')}.{activity_instance.get('minor_version')}"
                if activity_instance
                else None
            ),
            author_id=selection["author_id"],
            change_type=change_type,
            start_date=convert_to_datetime(value=selection["start_date"]),
            show_activity_instance_in_protocol_flowchart=selection[
                "show_activity_instance_in_protocol_flowchart"
            ],
            end_date=end_date,
        )

    def get_audit_trail_query(self, study_selection_uid: str):
        if study_selection_uid:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sa:StudyActivityInstance {uid: $study_selection_uid})
            WITH sa
            MATCH (sa)-[:AFTER|BEFORE*0..]-(all_sa:StudyActivityInstance)
            WITH distinct(all_sa)
            """
        else:
            audit_trail_cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sa:StudyActivityInstance)
            WITH DISTINCT all_sa
            """
        audit_trail_cypher += """

                    WITH DISTINCT all_sa
                    ORDER BY all_sa.uid ASC
                    MATCH (all_sa)<-[:AFTER]-(asa:StudyAction)
                    OPTIONAL MATCH (all_sa)<-[:BEFORE]-(bsa:StudyAction)
                    WITH all_sa, asa, bsa
                    ORDER BY all_sa.uid, asa.date DESC
                    RETURN
                        all_sa.uid AS study_selection_uid,
                        head(apoc.coll.sortMulti([(all_sa)<-[:STUDY_ACTIVITY_HAS_STUDY_ACTIVITY_INSTANCE]-(study_activity:StudyActivity)
                        -[:HAS_SELECTED_ACTIVITY]->(activity_value:ActivityValue)<-[has_version:HAS_VERSION]-(activity_root:ActivityRoot) | 
                            {
                                uid: study_activity.uid,
                                activity_uid: activity_root.uid,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1])
                            }], ['major_version', 'minor_version'])) AS study_activity,
                        head(apoc.coll.sortMulti([(all_sa)-[:HAS_SELECTED_ACTIVITY_INSTANCE]->(activity_instance_value:ActivityInstanceValue)
                            <-[has_version:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot) | 
                            {
                                uid: activity_instance_root.uid,
                                name:activity_instance_value.name,
                                major_version: toInteger(split(has_version.version,'.')[0]),
                                minor_version: toInteger(split(has_version.version,'.')[1])
                            }], ['major_version', 'minor_version'])) AS activity_instance,
                        coalesce(all_sa.show_activity_instance_in_protocol_flowchart, false) AS show_activity_instance_in_protocol_flowchart,
                        asa.date AS start_date,
                        asa.author_id AS author_id,
                        labels(asa) AS change_type,
                        bsa.date AS end_date
                    """
        return audit_trail_cypher

    def get_study_selection_node_from_latest_study_value(
        self, study_value: StudyValue, study_selection: StudySelection
    ):
        return study_value.has_study_activity_instance.get(
            uid=study_selection.study_selection_uid
        )

    def _add_new_selection(
        self,
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionActivityInstanceVO,
        audit_node: StudyAction,
        last_study_selection_node: StudyActivityInstance,
        for_deletion: bool = False,
    ):
        # Create new activity selection
        study_activity_instance_selection_node = StudyActivityInstance(
            show_activity_instance_in_protocol_flowchart=selection.show_activity_instance_in_protocol_flowchart,
            keep_old_version=selection.keep_old_version,
        )
        study_activity_instance_selection_node.uid = selection.study_selection_uid
        study_activity_instance_selection_node.accepted_version = (
            selection.accepted_version
        )
        study_activity_instance_selection_node.save()
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_activity_instance.connect(
                study_activity_instance_selection_node
            )
        # Connect new node with audit trail
        audit_node.has_after.connect(study_activity_instance_selection_node)
        if selection.activity_instance_uid:
            # find the activity instance value
            activity_instance_root_node: ActivityInstanceRoot = (
                ActivityInstanceRoot.nodes.get(uid=selection.activity_instance_uid)
            )
            latest_activity_instance_value_node: ActivityInstanceValue
            if selection.activity_instance_version:
                latest_activity_instance_value_node = (
                    activity_instance_root_node.get_value_for_version(
                        selection.activity_instance_version
                    )
                )
            else:
                latest_activity_instance_value_node = (
                    activity_instance_root_node.has_latest_value.get()
                )
            # Connect new node with Activity value
            study_activity_instance_selection_node.has_selected_activity_instance.connect(
                latest_activity_instance_value_node
            )

        # Connect StudyActivityInstance with StudyActivity node
        study_activity_node = StudyActivity.nodes.has(has_before=False).get(
            uid=selection.study_activity_uid
        )
        study_activity_instance_selection_node.study_activity_has_study_activity_instance.connect(
            study_activity_node
        )

        if last_study_selection_node:
            manage_previous_connected_study_selection_relationships(
                previous_item=last_study_selection_node,
                study_value_node=latest_study_value_node,
                new_item=study_activity_instance_selection_node,
                exclude_study_selection_relationships=[
                    StudyActivity,
                ],
            )

    def generate_uid(self) -> str:
        return StudyActivityInstance.get_next_free_uid_and_increment_counter()

    def close(self) -> None:
        pass

    def get_all_study_activity_instances_for_study_activity(
        self, study_uid: str, study_activity_uid
    ) -> list[StudyActivityInstance]:
        study_activity_instances = ListDistinct(
            StudyActivityInstance.nodes.filter(
                has_study_activity_instance__latest_value__uid=study_uid,
                study_activity_has_study_activity_instance__has_study_activity__latest_value__uid=study_uid,
                study_activity_has_study_activity_instance__uid=study_activity_uid,
            )
            .has(has_before=False)
            .resolve_subgraph()
        ).distinct()
        return study_activity_instances
