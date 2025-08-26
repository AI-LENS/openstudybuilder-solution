from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.concepts.utils import (
    list_concept_wildcard_properties,
)
from clinical_mdr_api.domain_repositories.models._utils import (
    format_generic_header_values,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGrouping,
    ActivityRoot,
    ActivityValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    CompactActivity,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    validate_filters_and_add_search_string,
)
from common.config import settings
from common.exceptions import BusinessLogicException
from common.utils import (
    convert_to_datetime,
    get_db_result_as_dict,
    version_string_to_tuple,
)


def _get_display_version(versions: list[dict[Any, Any]]) -> dict[Any, Any] | None:
    if len(versions) == 1:
        return versions[0]
    sorted_versions = sorted(
        versions, key=lambda x: version_string_to_tuple(x["version"]), reverse=True
    )
    for status in [
        LibraryItemStatus.FINAL,
        LibraryItemStatus.RETIRED,
        LibraryItemStatus.DRAFT,
    ]:
        latest_ver = next(
            (
                version
                for version in sorted_versions
                if version["status"] == status.value
            ),
            None,
        )
        if latest_ver:
            return latest_ver
    return None


class ActivityRepository(ConceptGenericRepository[ActivityAR]):
    root_class = ActivityRoot
    value_class = ActivityValue
    return_model = Activity
    filter_query_parameters: dict[Any, Any] = {}

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> ActivityAR:
        major, minor = input_dict.get("version").split(".")
        return ActivityAR.from_repository_values(
            uid=input_dict.get("uid"),
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=input_dict.get("nci_concept_id"),
                nci_concept_name=input_dict.get("nci_concept_name"),
                name=input_dict.get("name"),
                name_sentence_case=input_dict.get("name_sentence_case"),
                synonyms=input_dict.get("synonyms") or [],
                definition=input_dict.get("definition"),
                abbreviation=input_dict.get("abbreviation"),
                activity_groupings=[
                    ActivityGroupingVO(
                        activity_group_uid=activity_grouping.get("activity_group").get(
                            "uid"
                        ),
                        activity_group_name=activity_grouping.get("activity_group").get(
                            "name"
                        ),
                        activity_group_version=f"{activity_grouping.get('activity_group').get('major_version')}.{activity_grouping.get('activity_group').get('minor_version')}",
                        activity_subgroup_uid=activity_grouping.get(
                            "activity_subgroup"
                        ).get("uid"),
                        activity_subgroup_name=activity_grouping.get(
                            "activity_subgroup"
                        ).get("name"),
                        activity_subgroup_version=f"{activity_grouping.get('activity_subgroup').get('major_version')}.{activity_grouping.get('activity_subgroup').get('minor_version')}",
                    )
                    for activity_grouping in input_dict.get("activity_groupings")
                ],
                activity_instances=input_dict.get("activity_instances"),
                request_rationale=input_dict.get("request_rationale"),
                is_request_final=input_dict.get("is_request_final"),
                requester_study_id=input_dict.get("requester_study_id"),
                replaced_by_activity=input_dict.get("replaced_by_activity"),
                reason_for_rejecting=input_dict.get("reason_for_rejecting"),
                contact_person=input_dict.get("contact_person"),
                is_request_rejected=input_dict.get("is_request_rejected"),
                is_data_collected=input_dict.get("is_data_collected"),
                is_multiple_selection_allowed=input_dict.get(
                    "is_multiple_selection_allowed"
                ),
                is_finalized=input_dict.get("is_finalized"),
                is_used_by_legacy_instances=input_dict.get(
                    "is_used_by_legacy_instances"
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict.get("library_name"),
                is_library_editable_callback=(
                    lambda _: input_dict.get("is_library_editable")
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict.get("change_description"),
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict.get("author_id"),
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict.get("start_date")),
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
        study_count: int = 0,
        *,
        activity_root,
        **kwargs,
    ) -> ActivityAR:
        activity_groupings = []
        for activity_grouping in activity_root["activity_groupings"]:
            activity_group = activity_grouping["activity_group"]
            activity_subgroup = activity_grouping["activity_subgroup"]
            activity_groupings.append(
                ActivityGroupingVO(
                    activity_group_uid=activity_group.get("uid"),
                    activity_group_name=activity_group.get("name"),
                    activity_group_version=f"{activity_group.get('major_version')}.{activity_group.get('minor_version')}",
                    activity_subgroup_uid=activity_subgroup.get("uid"),
                    activity_subgroup_name=activity_subgroup.get("name"),
                    activity_subgroup_version=f"{activity_subgroup.get('major_version')}.{activity_subgroup.get('minor_version')}",
                )
            )

        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                synonyms=value.synonyms or [],
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=activity_root.get("activity_instances", []),
                request_rationale=value.request_rationale,
                is_request_final=(
                    value.is_request_final if value.is_request_final else False
                ),
                requester_study_id=activity_root["requester_study_id"],
                replaced_by_activity=activity_root["replaced_activity_uid"],
                reason_for_rejecting=value.reason_for_rejecting,
                contact_person=value.contact_person,
                is_request_rejected=(
                    value.is_request_rejected if value.is_request_rejected else False
                ),
                is_data_collected=(
                    value.is_data_collected if value.is_data_collected else False
                ),
                is_multiple_selection_allowed=(
                    value.is_multiple_selection_allowed
                    if value.is_multiple_selection_allowed is not None
                    else True
                ),
                is_finalized=bool(
                    value.is_request_rejected or activity_root["replaced_activity_uid"]
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library | None,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> ActivityAR:
        replaced_activity = value.replaced_by_activity.get_or_none()
        activity_groupings_nodes = value.has_grouping.all()
        activity_groupings = []
        activity_instances_legacy_codes = {}
        activity_instances = []
        _activity_instance_uids = set()
        for activity_grouping in activity_groupings_nodes:
            for activity_instance_value in activity_grouping.has_activity.all():
                has_version = activity_instance_value.has_version
                for activity_instance_root in has_version.all():
                    if activity_instance_root.uid in _activity_instance_uids:
                        continue
                    _activity_instance_uids.add(activity_instance_root.uid)
                    activity_instances.append(
                        {
                            "uid": activity_instance_root.uid,
                            "name": activity_instance_value.name,
                        }
                    )

                    has_version_props = has_version.relationship(activity_instance_root)
                    if (
                        activity_instance_root
                        and has_version_props.status == "Final"
                        and has_version_props.end_date is None
                        and activity_instance_root.uid
                        not in activity_instances_legacy_codes
                    ):
                        activity_instances_legacy_codes[activity_instance_root.uid] = (
                            activity_instance_value.is_legacy_usage
                        )

            activity_valid_groups = activity_grouping.in_subgroup.all()
            for activity_valid_group in activity_valid_groups:
                # ActivityGroup
                activity_group_value = activity_valid_group.in_group.get()
                activity_group_root = activity_group_value.has_version.single()
                all_group_rels = activity_group_value.has_version.all_relationships(
                    activity_group_root
                )
                latest_group = max(
                    all_group_rels, key=lambda r: version_string_to_tuple(r.version)
                )
                # ActivitySubGroup
                activity_subgroup_value = activity_valid_group.has_group.get()
                activity_subgroup_root = activity_subgroup_value.has_version.single()
                all_subgroup_rels = (
                    activity_subgroup_value.has_version.all_relationships(
                        activity_subgroup_root
                    )
                )
                latest_subgroup = max(
                    all_subgroup_rels, key=lambda r: version_string_to_tuple(r.version)
                )

                activity_groupings.append(
                    ActivityGroupingVO(
                        activity_group_uid=activity_group_root.uid,
                        activity_group_name=activity_group_value.name,
                        activity_group_version=latest_group.version,
                        activity_subgroup_uid=activity_subgroup_root.uid,
                        activity_subgroup_name=activity_subgroup_value.name,
                        activity_subgroup_version=latest_subgroup.version,
                    )
                )
        requester_study_id = None
        # We are only interested in the StudyId of the Activity Requests
        if library.name == settings.requested_library_name:
            if study_activity := value.has_selected_activity.single():
                if activity := study_activity.has_study_activity.single():
                    requester_study_id = (
                        f"{activity.study_id_prefix}-{activity.study_number}"
                    )
        return ActivityAR.from_repository_values(
            uid=root.uid,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=value.nci_concept_id,
                nci_concept_name=value.nci_concept_name,
                name=value.name,
                name_sentence_case=value.name_sentence_case,
                synonyms=value.synonyms or [],
                definition=value.definition,
                abbreviation=value.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=activity_instances,
                request_rationale=value.request_rationale,
                is_request_final=(
                    value.is_request_final if value.is_request_final else False
                ),
                requester_study_id=requester_study_id,
                replaced_by_activity=(
                    replaced_activity.uid if replaced_activity else None
                ),
                reason_for_rejecting=value.reason_for_rejecting,
                contact_person=value.contact_person,
                is_request_rejected=(
                    value.is_request_rejected if value.is_request_rejected else False
                ),
                is_data_collected=(
                    value.is_data_collected if value.is_data_collected else False
                ),
                is_multiple_selection_allowed=(
                    value.is_multiple_selection_allowed
                    if value.is_multiple_selection_allowed is not None
                    else True
                ),
                is_finalized=bool(value.is_request_rejected or replaced_activity),
                is_used_by_legacy_instances=(
                    all(activity_instances_legacy_codes.values())
                    if activity_instances_legacy_codes
                    else False
                ),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=(lambda _: library.is_editable),
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def create_query_filter_statement(
        self, library: str | None = None, **kwargs
    ) -> tuple[str, dict[Any, Any]]:
        (
            filter_statements_from_concept,
            filter_query_parameters,
        ) = super().create_query_filter_statement(library=library)
        filter_parameters = []
        activity_subgroup_uid = kwargs.get("activity_subgroup_uid")
        activity_group_uid = kwargs.get("activity_group_uid")
        if kwargs.get("group_by_groupings") is False:
            activity_grouping_query_text = "activity_grouping"
        else:
            activity_grouping_query_text = (
                "concept_value)-[:HAS_GROUPING]->(:ActivityGrouping"
            )
        if activity_subgroup_uid and activity_group_uid:
            filter_by_subgroup_and_group_uid = f"""
            {{activity_subgroup_uid: $activity_subgroup_uid, activity_group_uid: $activity_group_uid}} IN
            [({activity_grouping_query_text})-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup) |
            {{
                activity_subgroup_uid: head([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
                                            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]),
                activity_group_uid: head([(activity_valid_group)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
                                            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid])
            }}
            ]"""
            filter_parameters.append(filter_by_subgroup_and_group_uid)
            filter_query_parameters["activity_subgroup_uid"] = activity_subgroup_uid
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if activity_subgroup_uid is not None and activity_group_uid is None:
            filter_by_activity_subgroup_uid = f"""
            $activity_subgroup_uid IN [({activity_grouping_query_text})-[:IN_SUBGROUP]->
            (:ActivityValidGroup)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
            <-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot) | activity_subgroup_root.uid]"""
            filter_parameters.append(filter_by_activity_subgroup_uid)
            filter_query_parameters["activity_subgroup_uid"] = activity_subgroup_uid
        if activity_group_uid is not None and activity_subgroup_uid is None:
            filter_by_activity_group_uid = f"""
            $activity_group_uid IN [({activity_grouping_query_text})-[:IN_SUBGROUP]->
            (:ActivityValidGroup)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid]"""
            filter_parameters.append(filter_by_activity_group_uid)
            filter_query_parameters["activity_group_uid"] = activity_group_uid
        if kwargs.get("activity_names") is not None:
            activity_names = kwargs.get("activity_names")
            filter_by_activity_names = "concept_value.name IN $activity_names"
            filter_parameters.append(filter_by_activity_names)
            filter_query_parameters["activity_names"] = activity_names
        if kwargs.get("activity_subgroup_names") is not None:
            activity_subgroup_names = kwargs.get("activity_subgroup_names")
            filter_by_activity_subgroup_names = f"""
            size([({activity_grouping_query_text})-[:IN_SUBGROUP]->
            (:ActivityValidGroup)<-[:HAS_GROUP]-(asgv:ActivitySubGroupValue) WHERE asgv.name IN $activity_subgroup_names | asgv.name]) > 0"""
            filter_parameters.append(filter_by_activity_subgroup_names)
            filter_query_parameters["activity_subgroup_names"] = activity_subgroup_names
        if kwargs.get("activity_group_names") is not None:
            activity_group_names = kwargs.get("activity_group_names")
            filter_by_activity_group_names = f"""
            size([({activity_grouping_query_text})-[:IN_SUBGROUP]->
            (:ActivityValidGroup)-[:IN_GROUP]->(agv:ActivityGroupValue) WHERE agv.name IN $activity_group_names | agv.name]) > 0"""
            filter_parameters.append(filter_by_activity_group_names)
            filter_query_parameters["activity_group_names"] = activity_group_names
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

    def _create_new_value_node(self, ar: ActivityAR) -> ActivityValue:
        value_node: ActivityValue = super()._create_new_value_node(ar=ar)
        value_node.synonyms = ar.concept_vo.synonyms
        value_node.request_rationale = ar.concept_vo.request_rationale
        value_node.is_request_final = ar.concept_vo.is_request_final
        value_node.reason_for_rejecting = ar.concept_vo.reason_for_rejecting
        value_node.contact_person = ar.concept_vo.contact_person
        value_node.is_request_rejected = ar.concept_vo.is_request_rejected
        value_node.is_data_collected = ar.concept_vo.is_data_collected
        value_node.is_multiple_selection_allowed = (
            ar.concept_vo.is_multiple_selection_allowed
        )
        value_node.save()
        for activity_grouping in ar.concept_vo.activity_groupings:
            # create ActivityGrouping node
            activity_grouping_node = ActivityGrouping(
                uid=ActivityGrouping.get_next_free_uid_and_increment_counter()
            )
            activity_grouping_node.save()

            # link ActivityValue and ActivityGrouping nodes
            value_node.has_grouping.connect(activity_grouping_node)

            # find related ActivityValidGroup node
            query = """
                MATCH (activity_valid_group:ActivityValidGroup)-[:IN_GROUP]-(agv:ActivityGroupValue)<-[:HAS_VERSION]-(agr:ActivityGroupRoot {uid:$activity_group_uid})
                MATCH (activity_valid_group)-[:HAS_GROUP]-(asgv:ActivitySubGroupValue)<-[:HAS_VERSION]-(asgr:ActivitySubGroupRoot {uid:$activity_subgroup_uid})
                WITH *, 
                    head([(asgv)<-[latest:LATEST]-(asgr) | latest]) AS is_subgroup_latest,
                    head([(agv)<-[latest:LATEST]-(agr) | latest]) AS is_group_latest
                RETURN activity_valid_group
                ORDER BY is_subgroup_latest, is_group_latest
            """
            activity_valid_groups_ret, _ = db.cypher_query(
                query,
                params={
                    "activity_group_uid": activity_grouping.activity_group_uid,
                    "activity_subgroup_uid": activity_grouping.activity_subgroup_uid,
                },
                resolve_objects=True,
            )
            BusinessLogicException.raise_if(
                len(activity_valid_groups_ret) == 0,
                msg=f"The ActivityValidGroup node wasn't found for Activity Subgroup '{activity_grouping.activity_subgroup_uid}' "
                f"and Activity Group '{activity_grouping.activity_group_uid}'.",
            )
            activity_valid_group_node = activity_valid_groups_ret[0][0]
            # link ActivityGrouping and ActivityValidGroup
            activity_grouping_node.in_subgroup.connect(activity_valid_group_node)

        return value_node

    def _any_subgroup_updated(self, activity_value):
        for grouping_node in activity_value.has_grouping.all():
            if (
                not grouping_node.in_subgroup.get()
                .has_group.get()
                .has_latest_value.single()
            ):
                # The linked subgroup is not the latest.
                # We need to return True, so that the ActivityValue
                # gets updated to use the new subgroup value.
                return True
        return False

    def _has_data_changed(self, ar: ActivityAR, value: ActivityValue) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)
        are_props_changed = (
            ar.concept_vo.synonyms != value.synonyms
            or ar.concept_vo.request_rationale != value.request_rationale
            or ar.concept_vo.is_request_final != value.is_request_final
            or ar.concept_vo.reason_for_rejecting != value.reason_for_rejecting
            or ar.concept_vo.contact_person != value.contact_person
            or ar.concept_vo.is_request_rejected != value.is_request_rejected
            or ar.concept_vo.is_data_collected != value.is_data_collected
            or ar.concept_vo.is_multiple_selection_allowed
            != value.is_multiple_selection_allowed
        )

        activity_subgroup_uids = []
        activity_group_uids = []
        activity_grouping_nodes = value.has_grouping.all()
        for activity_grouping_node in activity_grouping_nodes:
            activity_valid_group_nodes = activity_grouping_node.in_subgroup.all()
            for activity_valid_group_node in activity_valid_group_nodes:
                activity_subgroup_uids.append(
                    activity_valid_group_node.has_group.get().has_version.single().uid
                )
                activity_group_uids.append(
                    activity_valid_group_node.in_group.get().has_version.single().uid
                )

        # Is this a final or retired version? If yes, we skip the check for updated subgroups
        # to avoid creating new values nodes when just creating a new draft.
        root_for_final_value = value.has_version.match(
            status__in=[LibraryItemStatus.FINAL.value, LibraryItemStatus.RETIRED.value],
            end_date__isnull=True,
        )
        if not root_for_final_value:
            subgroups_updated = self._any_subgroup_updated(value)
        else:
            subgroups_updated = False

        are_rels_changed = sorted(
            [
                activity_grouping.activity_group_uid
                for activity_grouping in ar.concept_vo.activity_groupings
            ]
        ) != sorted(activity_group_uids) or sorted(
            [
                activity_grouping.activity_subgroup_uid
                for activity_grouping in ar.concept_vo.activity_groupings
            ]
        ) != sorted(
            activity_subgroup_uids
        )
        return (
            are_concept_properties_changed
            or are_rels_changed
            or are_props_changed
            or subgroups_updated
        )

    @classmethod
    def format_filter_sort_keys(cls, key: str) -> str:
        """
        Maps a fieldname as provided by the API query (equal to output model) to the same fieldname as defined in the database and/or Cypher query

        :param key: Fieldname to map
        :return str:
        """
        if key.startswith("activity_groupings[0]."):
            splitted = key.split(".")
            activity_groupings_part = splitted[0]
            prop = splitted[1]
            if prop == "activity_group_name":
                return f"{activity_groupings_part}.activity_group.name"
            if prop == "activity_subgroup_name":
                return f"{activity_groupings_part}.activity_subgroup.name"
        if key in [
            "activity_group_uid",
            "activity_group_name",
            "activity_subgroup_uid",
            "activity_subgroup_name",
        ]:
            _split = key.rsplit("_", 1)
            return f"{_split[0]}.{_split[1]}"
        return key

    def specific_alias_clause(
        self, only_specific_status: str = ObjectStatus.LATEST.name, **kwargs
    ) -> str:
        # concept_value property comes from the main part of the query
        # which is specified in the concept_generic_repository
        activity_subgroup_names = self.filter_query_parameters.get(
            "activity_subgroup_names"
        )
        activity_group_names = self.filter_query_parameters.get("activity_group_names")

        if kwargs.get("group_by_groupings") is False:
            activity_grouping_query_text = "activity_grouping"
        else:
            activity_grouping_query_text = (
                "concept_value)-[:HAS_GROUPING]->(:ActivityGrouping"
            )
        return f"""
        WITH *,
            concept_value.synonyms AS synonyms,
            concept_value.request_rationale AS request_rationale,
            coalesce(concept_value.is_request_final, false) AS is_request_final,
            coalesce(concept_value.is_request_rejected, false) AS is_request_rejected,
            concept_value.contact_person AS contact_person,
            concept_value.reason_for_rejecting AS reason_for_rejecting,
            CASE
                WHEN library_name='Requested'
                THEN head([(concept_root)-[:HAS_VERSION]->(:{self.value_class.__label__})<-[:HAS_SELECTED_ACTIVITY]->(:StudyActivity)<-[:HAS_STUDY_ACTIVITY]-(study_value:StudyValue)
                   | coalesce(study_value.study_id_prefix, "") + "-" + toString(study_value.study_number)])
                ELSE NULL
            END AS requester_study_id,
            coalesce(concept_value.is_data_collected, False) AS is_data_collected,
            coalesce(concept_value.is_multiple_selection_allowed, True) AS is_multiple_selection_allowed,
            apoc.coll.toSet([({activity_grouping_query_text})-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            {'WHERE size([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value) WHERE activity_subgroup_value.name in $activity_subgroup_names | activity_subgroup_value.name]) > 0 '
        if activity_subgroup_names
        else ''}
            {'AND' if activity_subgroup_names and activity_group_names else ''}
            {'' if activity_subgroup_names and activity_group_names else 'WHERE' if not activity_subgroup_names and activity_group_names else ''}
            {'size([(activity_valid_group)-[:IN_GROUP]-(activity_group_value) WHERE activity_group_value.name in $activity_group_names | activity_group_value.name]) > 0 '
        if activity_group_names
        else ''}
             | {{
                 activity_subgroup: head(apoc.coll.sortMulti([(activity_valid_group)<-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)
                 <-[has_version:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
                    | {{
                        uid:activity_subgroup_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        name:activity_subgroup_value.name
                    }}], ['major_version', 'minor_version'])),
                    activity_group: head(apoc.coll.sortMulti([(activity_valid_group)-[:IN_GROUP]-(activity_group_value:ActivityGroupValue)
                    <-[has_version:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
                    | {{
                        uid:activity_group_root.uid,
                        major_version: toInteger(split(has_version.version,'.')[0]),
                        minor_version: toInteger(split(has_version.version,'.')[1]),
                        name:activity_group_value.name
                    }}], ['major_version', 'minor_version']))
                }}]) AS activity_groupings,
                apoc.coll.toSet([({activity_grouping_query_text})<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
                <-[has_version:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot) | {{uid: activity_instance_root.uid, name: activity_instance_value.name}}]) AS activity_instances,
                head([(concept_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root:ActivityRoot) | replacing_activity_root.uid]) AS replaced_by_activity,
                apoc.coll.sortMulti([({activity_grouping_query_text})<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
                    <-[instance_version:HAS_VERSION WHERE instance_version.status='Final' and instance_version.end_date IS NULL]-(activity_instance_root) |
                    {{
                        uid:activity_instance_root.uid,
                        legacy_code:activity_instance_value.is_legacy_usage,
                        major_version: toInteger(split(instance_version.version,'.')[0]),
                        minor_version: toInteger(split(instance_version.version,'.')[1])
                    }}], ['^uid', 'major_version', 'minor_version']) AS all_legacy_codes
                WITH *,
                    // Sort by uid and instance_version in descending order and leave only latest version of same ActivityInstances
                    [
                        i in range(0, size(all_legacy_codes) -1)
                        WHERE i=0 OR all_legacy_codes[i].uid <> all_legacy_codes[i-1].uid | all_legacy_codes[i].legacy_code ] as all_legacy_codes
                WITH *,
                    CASE
                    WHEN NOT is_request_rejected and replaced_by_activity IS NULL THEN false
                    ELSE true
                    END as is_finalized,
                    CASE WHEN size(all_legacy_codes) > 0
                        THEN all(is_legacy_usage IN all_legacy_codes where is_legacy_usage=true and is_legacy_usage IS NOT NULL)
                        ELSE false
                    END as is_used_by_legacy_instances
            """

    def _get_compact_activity_with_splitted_groupings_query(
        self, filter_statements: str
    ):
        match_clause = """
        MATCH (concept_root:ActivityRoot)-[:LATEST]->(concept_value:ActivityValue)
        MATCH (concept_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
        MATCH (activity_valid_group)-[:IN_GROUP]->(:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
        """
        match_clause += filter_statements

        alias_clause = """
        DISTINCT concept_root, concept_value, activity_grouping, activity_subgroup_root, activity_group_root
        CALL {
            WITH concept_root, concept_value
            MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
            WITH hv
            ORDER BY
                toInteger(split(hv.version, '.')[0]) ASC,
                toInteger(split(hv.version, '.')[1]) ASC,
                hv.end_date ASC,
                hv.start_date ASC
            WITH collect(hv) as hvs
            RETURN last(hvs) AS version_rel
        }
        WITH *,
            apoc.coll.sortMulti([(activity_grouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)
            <-[instance_version:HAS_VERSION WHERE instance_version.status='Final' and instance_version.end_date IS NULL]-(activity_instance_root:ActivityInstanceRoot) |
            {
                uid:activity_instance_root.uid,
                legacy_code:activity_instance_value.is_legacy_usage,
                major_version: toInteger(split(instance_version.version,'.')[0]),
                minor_version: toInteger(split(instance_version.version,'.')[1])
            }], ['^uid', 'major_version', 'minor_version']) AS all_legacy_codes
        WITH *,
            // Sort by uid and instance_version in descending order and leave only latest version of same ActivityInstances
            [
                i in range(0, size(all_legacy_codes) -1)
                WHERE i=0 OR all_legacy_codes[i].uid <> all_legacy_codes[i-1].uid | all_legacy_codes[i].legacy_code ] as all_legacy_codes
        WITH 
            concept_root.uid AS uid,
            concept_value.name AS name,
            concept_value.definition AS definition,
            concept_value.synonyms AS synonyms,
            concept_value.abbreviation AS abbreviation,
            coalesce(concept_value.is_data_collected, False) AS is_data_collected,
            version_rel.status AS status,
            activity_group_root.uid AS activity_group_uid,
            head([(:ActivityGroupRoot {uid:activity_group_root.uid})-[:LATEST]->(activity_group_value:ActivityGroupValue) | activity_group_value.name]) as activity_group_name,
            activity_subgroup_root.uid AS activity_subgroup_uid,
            head([(:ActivitySubGroupRoot {uid:activity_subgroup_root.uid})-[:LATEST]->(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name]) as activity_subgroup_name,
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library.name]) AS library_name,
            CASE WHEN size(all_legacy_codes) > 0
                THEN all(is_legacy_usage IN all_legacy_codes where is_legacy_usage=true and is_legacy_usage IS NOT NULL)
                ELSE false
            END as is_used_by_legacy_instances
        """
        return match_clause, alias_clause

    def get_compact_activity_with_splitted_groupings(
        self,
        library: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        total_count: bool = False,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Concept aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param library:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :param return_all_versions:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library,
        )

        self.filter_query_parameters = filter_query_parameters
        match_clause, alias_clause = (
            self._get_compact_activity_with_splitted_groupings_query(
                filter_statements=filter_statements
            )
        )
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=CompactActivity,
        )
        query.parameters.update(filter_query_parameters)

        result_array, attributes_names = query.execute()

        items = [get_db_result_as_dict(row, attributes_names) for row in result_array]

        count_result, _ = db.cypher_query(
            query=query.count_query, params=query.parameters
        )
        total_amount = (
            count_result[0][0] if len(count_result) > 0 and total_count else 0
        )

        return items, total_amount

    def get_compact_activity_with_splitted_groupings_distinct_headers(
        self,
        field_name: str,
        search_string: str | None = "",
        library: str | None = None,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator | None = FilterOperator.AND,
        page_size: int = 10,
        **kwargs,
    ) -> list[Any]:
        # pylint: disable=unused-argument
        """
        Method runs a cypher query to fetch possible values for a given field_name, with a limit of page_size.
        It uses generic filtering capability, on top of filtering the field_name with provided search_string.

        :param field_name: Field name for which to return possible values
        :param search_string
        :param library:
        :param filter_by:
        :param filter_operator: Same as for generic filtering
        :param page_size: Max number of values to return. Default 10
        :return list[Any]:
        """

        # Add header field name to filter_by, to filter with a CONTAINS pattern
        filter_by = validate_filters_and_add_search_string(
            search_string, field_name, filter_by
        )
        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library,
        )
        match_clause, alias_clause = (
            self._get_compact_activity_with_splitted_groupings_query(
                filter_statements=filter_statements
            )
        )

        # Use Cypher query class to use reusable helper methods
        query = CypherQueryBuilder(
            filter_by=FilterDict(elements=filter_by),
            filter_operator=filter_operator,
            match_clause=match_clause,
            alias_clause=alias_clause,
            return_model=CompactActivity,
            wildcard_properties_list=list_concept_wildcard_properties(CompactActivity),
        )

        query.parameters.update(filter_query_parameters)
        query.full_query = query.build_header_query(
            header_alias=field_name, page_size=page_size
        )
        result_array, _ = query.execute()

        return (
            format_generic_header_values(result_array[0][0])
            if len(result_array) > 0
            else []
        )

    def replace_request_with_sponsor_activity(
        self, activity_request_uid: str, sponsor_activity_uid: str
    ) -> None:
        replace_activity_request_with_sponsor_activity_query = """
            MATCH (:ActivityRoot {uid: $activity_request_uid})-[:LATEST]->(activity_request_value:ActivityValue)
            MATCH (replacing_activity_root:ActivityRoot {uid: $sponsor_activity_uid})
            WITH activity_request_value, replacing_activity_root
            MERGE (activity_request_value)-[:REPLACED_BY_ACTIVITY]->(replacing_activity_root)
        """
        db.cypher_query(
            replace_activity_request_with_sponsor_activity_query,
            {
                "activity_request_uid": activity_request_uid,
                "sponsor_activity_uid": sponsor_activity_uid,
            },
        )

    def final_or_replaced_retired_activity_exists(self, uid: str) -> bool:
        query = f"""
            MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_FINAL]->(concept_value)
            RETURN concept_root
            """
        result, _ = db.cypher_query(query, {"uid": uid})
        exists = len(result) > 0 and len(result[0]) > 0
        if not exists:
            query = f"""
                MATCH (concept_root:{self.root_class.__label__} {{uid: $uid}})-[:LATEST_RETIRED]->(concept_value)
                -[:REPLACED_BY_ACTIVITY]->(:ActivityRoot)
                RETURN concept_root
                """
            result, _ = db.cypher_query(query, {"uid": uid})
            exists = len(result) > 0 and len(result[0]) > 0
        return exists

    def get_activity_overview(
        self, uid: str, version: str | None = None
    ) -> dict[str, Any]:
        if version:
            params = {"uid": uid, "version": version}
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})
                CALL {
                        WITH activity_root
                        MATCH (activity_root)-[hv:HAS_VERSION {version:$version}]->(av:ActivityValue)
                        WITH hv, av
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs, collect (av) as avs
                        RETURN last(hvs) as has_version, last(avs) as activity_value
                    }
                """
        else:
            params = {"uid": uid}
            match = """
                    MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
                    CALL {
                        WITH activity_root, activity_value
                        MATCH (activity_root)-[hv:HAS_VERSION]-(activity_value)
                        WITH hv
                        ORDER BY
                            toInteger(split(hv.version, '.')[0]) ASC,
                            toInteger(split(hv.version, '.')[1]) ASC,
                            hv.end_date ASC,
                            hv.start_date ASC
                        WITH collect(hv) as hvs
                        RETURN last(hvs) as has_version
                    }
                    """
        query = (
            match
            + """
        WITH DISTINCT activity_root,activity_value, has_version,
            head([(library)-[:CONTAINS_CONCEPT]->(activity_root) | library.name]) AS activity_library_name,
            [(activity_root)-[versions:HAS_VERSION]->(:ActivityValue) | versions.version] as all_versions,
            apoc.coll.sortMulti([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)<-[aihv:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot)
            WHERE NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
            | {
                activity_instance_library_name: head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]),
                uid: activity_instance_root.uid,
                version: 
                    {
                        major_version: toInteger(split(aihv.version,'.')[0]),
                        minor_version: toInteger(split(aihv.version,'.')[1]),
                        status:aihv.status
                    },
                name:activity_instance_value.name,
                name_sentence_case:activity_instance_value.name_sentence_case,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                adam_param_code:activity_instance_value.adam_param_code,
                is_required_for_activity:coalesce(activity_instance_value.is_required_for_activity, false),
                is_default_selected_for_activity:coalesce(activity_instance_value.is_default_selected_for_activity, false),
                is_data_sharing:coalesce(activity_instance_value.is_data_sharing, false),
                is_legacy_usage:coalesce(activity_instance_value.is_legacy_usage, false),
                is_derived:coalesce(activity_instance_value.is_derived, false),
                topic_code:activity_instance_value.topic_code,
                activity_instance_class: head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->(activity_instance_class_root:ActivityInstanceClassRoot)
                    -[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) | activity_instance_class_value])
                }], ['^uid', 'version.major_version', 'version.minor_version']) AS activity_instances,
                apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
                    <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
                    | {
                        activity_subgroup_value: activity_subgroup_value,
                        activity_subgroup_uid: activity_subgroup_root.uid,
                        activity_group_value: head([(activity_valid_group)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
                            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_value]),
                        activity_group_uid: head([(activity_valid_group)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)
                            <-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot) | activity_group_root.uid])
                    }]) AS hierarchy
            RETURN
                hierarchy,
                activity_root,
                activity_value,
                activity_library_name,
                apoc.coll.sortMaps(activity_instances, '^name') as activity_instances,
                has_version,
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
        )
        result_array, attribute_names = db.cypher_query(query=query, params=params)
        BusinessLogicException.raise_if(
            len(result_array) != 1,
            msg=f"The overview query returned broken data: {result_array}",
        )
        overview = result_array[0]
        overview_dict = {}
        for overview_prop, attribute_name in zip(overview, attribute_names):
            overview_dict[attribute_name] = overview_prop
        return overview_dict

    def get_cosmos_activity_overview(self, uid: str) -> dict[str, Any]:
        query = """
        MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
        WITH DISTINCT activity_root,activity_value,
            apoc.coll.toSet([(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)-[:ACTIVITY_INSTANCE_CLASS]->
            (activity_instance_class_root:ActivityInstanceClassRoot)-[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue)
            WHERE NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
            | {
                name:activity_instance_value.name,
                nci_concept_id:activity_instance_value.nci_concept_id,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                activity_instance_class_name: activity_instance_class_value.name
            }]) AS activity_instances,
            [(activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
            <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue) | activity_subgroup_value.name] AS activity_subgroups
        WITH activity_root, activity_value,
            activity_subgroups,
            apoc.coll.sortMaps(activity_instances, '^name') as activity_instances
        OPTIONAL MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value)-[:CONTAINS_ACTIVITY_ITEM]->
            (activity_item:ActivityItem)<-[:HAS_ACTIVITY_ITEM]-(activity_item_class_root:ActivityItemClassRoot)-[:LATEST]->
            (activity_item_class_value:ActivityItemClassValue)
        OPTIONAL MATCH (activity_item)-[]->(CTTermRoot)-[:HAS_ATTRIBUTES_ROOT]->(CTTermAttributesRoot)-[:LATEST]->(activity_item_term_attr_value)
        OPTIONAL MATCH (activity_item)-[:HAS_UNIT_DEFINITION]->(:UnitDefinitionRoot)-[:LATEST]->(unit_def:UnitDefinitionValue)
        WITH activity_root, activity_value,
            activity_item_class_value,
            activity_instances,
            activity_subgroups,
            CASE WHEN size(collect(activity_item)) > 0 THEN
            apoc.map.fromPairs([
                ['nci_concept_id', activity_item_class_value.nci_concept_id],
                ['name', activity_item_class_value.name],
                ['type', head([(activity_item_class_value)-[:HAS_DATA_TYPE]->(data_type_term_root)-[:HAS_ATTRIBUTES_ROOT]->(data_type_term_attr_root)-[:LATEST]->(data_type_term_attr_value) | data_type_term_attr_value.preferred_term])],
                ['example_set', collect(distinct(coalesce(activity_item_term_attr_value.code_submission_value, unit_def.name)))]
            ]) ELSE null
            END
            AS activity_items
        RETURN
            activity_subgroups,
            {
                uid: activity_root.uid,
                name: activity_value.name,
                name_sentence_case: activity_value.name_sentence_case,
                definition: activity_value.definition,
                abbreviation: activity_value.abbreviation,
                nci_concept_id: activity_value.nci_concept_id
            } AS activity_value,
            activity_instances,
            collect(activity_items) AS activity_items
        """
        result_array, attribute_names = db.cypher_query(
            query=query, params={"uid": uid}
        )
        BusinessLogicException.raise_if(
            len(result_array) != 1,
            msg=f"The overview query returned broken data: {result_array}",
        )
        return {
            attribute_name: result_array[0][index]
            for index, attribute_name in enumerate(attribute_names)
        }

    def generic_match_clause(
        self,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ):
        concept_label = self.root_class.__label__
        concept_value_label = self.value_class.__label__
        query = f"""CYPHER runtime=slotted MATCH (concept_root:{concept_label})-[:{only_specific_status}]->(concept_value:{concept_value_label})
        """
        # IF group_by_groupings false THEN add grouping granularity
        if kwargs.get("group_by_groupings") is False:
            # OPTIONAL because not all activities have groupings
            query += """OPTIONAL MATCH (concept_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)
                MATCH (concept_value)
            """
        return query

    def generic_alias_clause(self, **kwargs):
        return f"""
            DISTINCT concept_root, concept_value, {"activity_grouping," if kwargs.get("group_by_groupings") is False else ""}
            head([(library)-[:CONTAINS_CONCEPT]->(concept_root) | library]) AS library
            CALL {{
                WITH concept_root, concept_value
                MATCH (concept_root)-[hv:HAS_VERSION]-(concept_value)
                WITH hv
                ORDER BY
                    toInteger(split(hv.version, '.')[0]) ASC,
                    toInteger(split(hv.version, '.')[1]) ASC,
                    hv.start_date ASC
                WITH collect(hv) as hvs
                RETURN last(hvs) AS version_rel
            }}
            CALL {{
                WITH version_rel
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = version_rel.author_id
                RETURN author
            }}
            WITH
                {"activity_grouping," if kwargs.get("group_by_groupings") is False else ""}
                concept_root.uid AS uid,
                concept_root,
                concept_value.nci_concept_id AS nci_concept_id,
                concept_value.nci_concept_name AS nci_concept_name,
                concept_value.name AS name,
                concept_value.name_sentence_case AS name_sentence_case,
                concept_value.external_id AS external_id,
                concept_value.definition AS definition,
                concept_value.abbreviation AS abbreviation,
                CASE WHEN concept_value:TemplateParameterTermValue THEN true ELSE false END AS template_parameter,
                library.name AS library_name,
                library.is_editable AS is_library_editable,
                version_rel.start_date AS start_date,
                version_rel.end_date AS end_date,
                version_rel.status AS status,
                version_rel.version AS version,
                version_rel.change_description AS change_description,
                version_rel.author_id AS author_id,
                coalesce(author.username, version_rel.author_id) AS author_username,
                concept_value
        """

    def generic_match_clause_all_versions(self):
        return """
            MATCH (concept_root:ActivityRoot)-[version:HAS_VERSION]->(concept_value:ActivityValue)
                    -[:HAS_GROUPING]->(ag:ActivityGrouping)
                    -[:IN_SUBGROUP]->(avg:ActivityValidGroup)<-[:HAS_GROUP]-(subgroup_val:ActivitySubGroupValue)<-[:HAS_VERSION]-(subgroup_root:ActivitySubGroupRoot)
            WITH *
            MATCH (avg)-[:IN_GROUP]->(group_value:ActivityGroupValue)<-[:HAS_VERSION]-(group_root:ActivityGroupRoot)
        """

    def is_multiple_selection_allowed_for_activity(self, activity_uid: str) -> bool:
        query = """
            MATCH (activity_root:ActivityRoot {uid: $activity_uid})-[:LATEST_FINAL]->(activity_value)
            RETURN coalesce(activity_value.is_multiple_selection_allowed, true)
            """
        result, _ = db.cypher_query(query, {"activity_uid": activity_uid})
        is_multiple_selection_allowed_for_activity = (
            len(result) > 0 and len(result[0]) > 0
        )
        return is_multiple_selection_allowed_for_activity

    def get_linked_upgradable_activity_instances(
        self, uid: str, version: str | None = None
    ) -> dict[Any, Any] | None:
        # Get "upgradable" linked activity instance values.
        # These are the instance values that have no end date,
        # meaning that the linked value is the latest version of the instance.
        params = {"uid": uid}
        if version:
            params["version"] = version
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})-[hv:HAS_VERSION {version:$version}]->(activity_value:ActivityValue)
                WITH DISTINCT activity_root, activity_value
                """
        else:
            match = """
                MATCH (activity_root:ActivityRoot {uid:$uid})-[:LATEST]->(activity_value:ActivityValue)
                """

        query = (
            match
            + """
        MATCH (activity_value)-[:HAS_GROUPING]->(activity_grouping:ActivityGrouping)<-[:HAS_ACTIVITY]-
            (activity_instance_value:ActivityInstanceValue)<-[aihv:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot)
        OPTIONAL MATCH (activity_grouping)-[:IN_SUBGROUP]->(activity_valid_group:ActivityValidGroup)
        <-[:HAS_GROUP]-(activity_subgroup_value:ActivitySubGroupValue)<-[:HAS_VERSION]-(activity_subgroup_root:ActivitySubGroupRoot)
        OPTIONAL MATCH (activity_valid_group)-[:IN_GROUP]->(activity_group_value:ActivityGroupValue)<-[:HAS_VERSION]-(activity_group_root:ActivityGroupRoot)
        WITH DISTINCT activity_root, activity_value, activity_instance_root, activity_instance_value, aihv, COLLECT(DISTINCT {
            activity_uid: activity_root.uid,
            activity_group_uid: activity_group_root.uid,
            activity_subgroup_uid: activity_subgroup_root.uid
        }) AS activity_groupings
        WHERE aihv.end_date IS NULL AND NOT EXISTS ((activity_instance_value)<--(:DeletedActivityInstanceRoot))
        WITH *,
            {
                activity_instance_library_name: head([(library)-[:CONTAINS_CONCEPT]->(activity_instance_root) | library.name]),
                uid: activity_instance_root.uid,
                version: 
                    {
                        major_version: toInteger(split(aihv.version,'.')[0]),
                        minor_version: toInteger(split(aihv.version,'.')[1]),
                        status:aihv.status
                    },
                name:activity_instance_value.name,
                name_sentence_case:activity_instance_value.name_sentence_case,
                abbreviation:activity_instance_value.abbreviation,
                definition:activity_instance_value.definition,
                adam_param_code:activity_instance_value.adam_param_code,
                is_required_for_activity:coalesce(activity_instance_value.is_required_for_activity, false),
                is_default_selected_for_activity:coalesce(activity_instance_value.is_default_selected_for_activity, false),
                is_data_sharing:coalesce(activity_instance_value.is_data_sharing, false),
                is_legacy_usage:coalesce(activity_instance_value.is_legacy_usage, false),
                is_derived:coalesce(activity_instance_value.is_derived, false),
                topic_code:activity_instance_value.topic_code,
                activity_instance_class: head([(activity_instance_value)-[:ACTIVITY_INSTANCE_CLASS]->(activity_instance_class_root:ActivityInstanceClassRoot)
                    -[:LATEST]->(activity_instance_class_value:ActivityInstanceClassValue) | activity_instance_class_value]),
                activity_groupings: activity_groupings
            } AS activity_instance ORDER BY activity_instance.uid, activity_instance.name
        RETURN
            collect(activity_instance) as activity_instances
        """
        )
        result_array, attribute_names = db.cypher_query(query=query, params=params)
        if len(result_array) == 0:
            return None
        BusinessLogicException.raise_if(
            len(result_array) > 1,
            msg=f"The linked instances query returned broken data: {result_array}",
        )
        instances = result_array[0]
        instances_dict = {}
        for instances_prop, attribute_name in zip(instances, attribute_names):
            instances_dict[attribute_name] = instances_prop
        return instances_dict

    def get_activity_uids_by_synonyms(self, synonyms: list[str]):
        if not synonyms:
            return {}

        rs = db.cypher_query(
            """
MATCH(r:ActivityRoot)-[:LATEST]->(v:ActivityValue)
WHERE ANY(value IN $syn WHERE value IN v.synonyms)
RETURN r.uid, [value IN $syn WHERE value IN v.synonyms] as existingSynonyms
""",
            params={"syn": synonyms},
        )

        if not rs[0]:
            return {}

        return {item[0]: item[1] for item in rs[0]}

    def get_specific_activity_version_groupings(
        self,
        uid: str,
        version: str,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> GenericFilteringReturn:
        """
        Get activity groupings information for a specific version of an activity, including
        related subgroups, groups, and instances that existed during this version's validity period.
        """
        query = """
            // 1. Find a specific activity version
            MATCH (ar:ActivityRoot {uid: $uid})-[av_rel:HAS_VERSION {version: $version}]->(av:ActivityValue)

            // 2. Find when this version's validity ends (either its end_date or the start of the next version)
            OPTIONAL MATCH (ar)-[next_rel:HAS_VERSION]->(next_av:ActivityValue)
            WHERE toFloat(next_rel.version) > toFloat(av_rel.version)
            WITH av, ar, av_rel, 
                 CASE WHEN av_rel.end_date IS NULL 
                      THEN min(next_rel.start_date) 
                      ELSE av_rel.end_date 
                 END as version_end_date

            // 3. Find all subgroup and group versions connected to it
            MATCH (av)-[:HAS_GROUPING]->(agrp:ActivityGrouping)-[:IN_SUBGROUP]->(avg:ActivityValidGroup)
            MATCH (avg)-[:IN_GROUP]->(gv:ActivityGroupValue)<-[gv_rel:HAS_VERSION]-(gr:ActivityGroupRoot)
            MATCH (avg)<-[:HAS_GROUP]-(sgv:ActivitySubGroupValue)<-[sgv_rel:HAS_VERSION]-(sgr:ActivitySubGroupRoot)

            // Filter versions that existed when the activity was created
            WHERE sgv_rel.start_date <= av_rel.start_date AND gv_rel.start_date <= av_rel.start_date

            WITH av, ar, av_rel, sgv, sgv_rel, gv, gv_rel, gr, sgr, avg, version_end_date

            // 4. Find activity instances connected to this activity via groupings
            OPTIONAL MATCH (avg)<-[:IN_SUBGROUP]-(agrp:ActivityGrouping)<-[:HAS_ACTIVITY]-(activity_instance_value:ActivityInstanceValue)<-[aihv:HAS_VERSION]-(activity_instance_root:ActivityInstanceRoot)

            // Make sure the instance is connected to this specific activity
            WHERE EXISTS {
                (activity_instance_value)-[:HAS_ACTIVITY]->(agrp2:ActivityGrouping)-[:HAS_GROUPING]-(av)
            }
            AND aihv.start_date <= COALESCE(version_end_date, datetime())
            AND NOT EXISTS((activity_instance_value)<--(:DeletedActivityInstanceRoot))

            // 5. Collect all relevant data for processing
            WITH 
                ar.uid as activity_uid, 
                av_rel.version as activity_version,
                avg.uid as valid_group_uid,
                sgr.uid as subgroup_uid, 
                gr.uid as group_uid,
                sgv_rel.version as subgroup_version,
                gv_rel.version as group_version,
                sgv.name as subgroup_name,
                gv.name as group_name,
                sgv_rel.status as subgroup_status,
                gv_rel.status as group_status,
                toInteger(SPLIT(sgv_rel.version, '.')[0]) as sg_major_version,
                toInteger(SPLIT(sgv_rel.version, '.')[1]) as sg_minor_version,
                toInteger(SPLIT(gv_rel.version, '.')[0]) as g_major_version,
                toInteger(SPLIT(gv_rel.version, '.')[1]) as g_minor_version,
                collect(DISTINCT {
                    instance_uid: activity_instance_root.uid,
                    instance_name: activity_instance_value.name
                }) as activity_instances

            // 6. For each valid group, collect all version information
            WITH 
                activity_uid, 
                activity_version, 
                valid_group_uid, 
                subgroup_uid, 
                group_uid,
                collect({
                    sg_major: sg_major_version, 
                    sg_minor: sg_minor_version, 
                    g_major: g_major_version, 
                    g_minor: g_minor_version,
                    subgroup_version: subgroup_version, 
                    group_version: group_version,
                    subgroup_name: subgroup_name, 
                    group_name: group_name,
                    subgroup_status: subgroup_status,
                    group_status: group_status
                }) as versions,
                activity_instances

            // 7. Find highest major version
            WITH 
                activity_uid, 
                activity_version, 
                valid_group_uid, 
                subgroup_uid, 
                group_uid, 
                versions,
                reduce(max_sg_major = 0, v IN versions | 
                    CASE WHEN v.sg_major > max_sg_major THEN v.sg_major ELSE max_sg_major END
                ) as max_sg_major,
                reduce(max_g_major = 0, v IN versions | 
                    CASE WHEN v.g_major > max_g_major THEN v.g_major ELSE max_g_major END
                ) as max_g_major,
                activity_instances

            // 8. Filter to only include versions with the maximum major version
            WITH 
                activity_uid, 
                activity_version, 
                valid_group_uid, 
                subgroup_uid, 
                group_uid, 
                [v in versions WHERE v.sg_major = max_sg_major] as sg_max_major_versions,
                [v in versions WHERE v.g_major = max_g_major] as g_max_major_versions,
                max_sg_major, 
                max_g_major,
                activity_instances

            // 9. Find highest minor version
            WITH 
                activity_uid, 
                activity_version, 
                valid_group_uid, 
                subgroup_uid, 
                group_uid, 
                max_sg_major, 
                max_g_major,
                reduce(max_sg_minor = -1, v IN sg_max_major_versions | 
                    CASE WHEN v.sg_minor > max_sg_minor THEN v.sg_minor ELSE max_sg_minor END
                ) as max_sg_minor,
                reduce(max_g_minor = -1, v IN g_max_major_versions | 
                    CASE WHEN v.g_minor > max_g_minor THEN v.g_minor ELSE max_g_minor END
                ) as max_g_minor,
                sg_max_major_versions, 
                g_max_major_versions,
                activity_instances

            // 10. Extract the specific version information
            WITH 
                activity_uid, 
                activity_version, 
                valid_group_uid, 
                subgroup_uid, 
                group_uid, 
                max_sg_major, 
                max_sg_minor, 
                max_g_major, 
                max_g_minor,
                [v in sg_max_major_versions WHERE v.sg_minor = max_sg_minor][0] as sg_version_info,
                [v in g_max_major_versions WHERE v.g_minor = max_g_minor][0] as g_version_info,
                activity_instances

            // 11. Return data
            RETURN 
                activity_uid, 
                activity_version, 
                valid_group_uid,
                subgroup_uid, 
                sg_version_info.subgroup_name as subgroup_name, 
                sg_version_info.subgroup_version as subgroup_version,
                sg_version_info.subgroup_status as subgroup_status,
                group_uid, 
                g_version_info.group_name as group_name, 
                g_version_info.group_version as group_version,
                g_version_info.group_status as group_status,
                activity_instances
            """

        result_array, _ = db.cypher_query(
            query=query, params={"uid": uid, "version": version}
        )

        BusinessLogicException.raise_if(
            len(result_array) == 0,
            msg=f"No data found for activity {uid} version {version}",
        )

        # Process the result into a structured format
        activity_groupings = []
        all_activity_instances = set()
        seen_instance_uids = set()  # Track UIDs we've already processed

        for row in result_array:
            (
                _,  # activity_uid (unused)
                _,  # activity_version (unused)
                valid_group_uid,
                subgroup_uid,
                subgroup_name,
                subgroup_version,
                subgroup_status,
                group_uid,
                group_name,
                group_version,
                group_status,
                activity_instances,
            ) = row

            # Process instances - filtering out None values and duplicates
            group_instances = []
            for instance in activity_instances:
                if (
                    instance["instance_uid"] is not None
                    and instance["instance_uid"] not in seen_instance_uids
                ):

                    # Mark this UID as seen
                    seen_instance_uids.add(instance["instance_uid"])

                    # Add to the specific group's instances
                    group_instances.append(
                        {
                            "uid": instance["instance_uid"],
                            "name": instance["instance_name"],
                        }
                    )
                    # Also track for the global list (backward compatibility)
                    all_activity_instances.add(
                        (instance["instance_uid"], instance["instance_name"])
                    )

            # Add grouping information with its specific instances
            activity_groupings.append(
                {
                    "valid_group_uid": valid_group_uid,
                    "subgroup": {
                        "uid": subgroup_uid,
                        "name": subgroup_name,
                        "version": subgroup_version,
                        "status": subgroup_status,
                    },
                    "group": {
                        "uid": group_uid,
                        "name": group_name,
                        "version": group_version,
                        "status": group_status,
                    },
                    "activity_instances": group_instances,
                }
            )

        # Convert activity instances to list of dictionaries
        activity_instances_list = [
            {"uid": uid, "name": name}
            for uid, name in all_activity_instances
            if uid is not None
        ]

        # Handle pagination if requested
        if page_size > 0:
            total = len(activity_groupings) if total_count else None
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            paginated_groupings = activity_groupings[start_idx:end_idx]

            # Return paginated results with GenericFilteringReturn.create()
            items = [
                {
                    "activity_uid": uid,
                    "activity_version": version,
                    "activity_groupings": paginated_groupings,
                    "activity_instances": activity_instances_list,
                }
            ]
            return GenericFilteringReturn.create(
                items=items, total=total or len(paginated_groupings)
            )

        # For backward compatibility, wrap single item in GenericFilteringReturn
        item = {
            "activity_uid": uid,
            "activity_version": version,
            "activity_groupings": activity_groupings,
            "activity_instances": activity_instances_list,
        }
        return GenericFilteringReturn.create(items=[item], total=1)

    def get_activity_instances_for_version(
        self,
        activity_uid: str,
        version: str | None,
        skip: int = 0,
        limit: int = 10,
    ) -> tuple[list[dict[Any, Any]], int]:
        """
        Retrieves a paginated list of activity instances relevant to a specific
        activity version's time validity window.

        For each relevant activity instance, it returns the latest version active
        during the activity version's timeframe, along with all its older versions
        as children.

        Args:
            activity_uid (str): The UID of the parent activity.
            version (str): The specific version of the parent activity (e.g., "16.0").
            skip (int): Number of records to skip for pagination (0-based).
            limit (int): Maximum number of records to return.

        Returns:
            tuple[list[dict], int]: A tuple containing the list of activity instance
                                    dictionaries and the total count of unique relevant instances.
        """
        # Ensure skip and limit are non-negative integers
        if not isinstance(skip, int) or skip < 0:
            skip = 0

        # Store original limit for pagination logic
        original_page_size = limit

        if not isinstance(limit, int) or limit < 0:
            # Default to a reasonable value for negative or invalid values
            limit = 10

        # Query 1: Calculate version_end_date and count total relevant roots
        count_and_end_date_query = """
            // 1a. Find the specific activity version
            MATCH (activity_root:ActivityRoot {uid: $uid})-[av_rel:HAS_VERSION {version: $version}]->(activity_value:ActivityValue)
            WITH activity_root, av_rel, activity_value

            // 1b. Find the minimum start date of subsequent versions (if any)
            OPTIONAL MATCH (activity_root)-[next_rel:HAS_VERSION]->(:ActivityValue)
            WHERE toFloat(next_rel.version) > toFloat($version) // Use parameter
            WITH activity_value, av_rel, min(next_rel.start_date) as min_next_start_date // Grouping implicitly by activity_value, av_rel

            // 1c. Calculate the final version_end_date
            WITH activity_value, COALESCE(av_rel.end_date, min_next_start_date, datetime()) as version_end_date

            // 2. Find distinct relevant ActivityInstance Roots and count them
            MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(:ActivityInstanceValue)<-[aihv_check:HAS_VERSION]-(ai_root:ActivityInstanceRoot)
            // *** NOTE: Add appropriate deletion check here if needed, e.g.: ***
            // WHERE NOT coalesce(ai_root.is_deleted, false)
            // AND NOT EXISTS((activity_instance_value)<--(:DeletedActivityInstanceRoot))
            WHERE aihv_check.start_date <= version_end_date
            RETURN count(DISTINCT ai_root) as total_count, version_end_date
        """
        params_count = {"uid": activity_uid, "version": version}
        try:
            count_result, _ = db.cypher_query(
                query=count_and_end_date_query,
                params=params_count,
                resolve_objects=False,
            )
            if not count_result or not count_result[0]:
                # This case might mean the activity/version doesn't exist or has no linked instances
                return [], 0
            total_count = count_result[0][0]
            version_end_date = count_result[0][1]  # Get the calculated end date

            # Handle case where activity/version exists but no instances meet criteria
            if total_count == 0:
                return [], 0

        except IndexError:
            # Handle case where query returns empty results unexpectedly
            return [], 0
        except Exception as e:
            # Log error or raise a more specific exception
            print(f"Error executing count/end_date query: {e}")
            raise  # Re-raise for now, or handle appropriately

        # Query 2: Fetch details for paginated roots

        # Build pagination clause based on original page size
        pagination_clause = ""
        if original_page_size > 0:
            pagination_clause = f"""
            // 3. Apply Pagination to the distinct relevant roots
            ORDER BY ai_root.uid
            SKIP {skip}
            LIMIT {limit}
            """
        else:
            pagination_clause = """
            // 3. Apply ordering but no pagination (return all items)
            ORDER BY ai_root.uid
            """

        details_query = f"""
            // 1. Find the specific activity version's value node
            MATCH (activity_root:ActivityRoot {{uid: $uid}})-[:HAS_VERSION {{version: $version}}]->(activity_value:ActivityValue)
            WITH activity_value, $version_end_date as version_end_date // Pass calculated end date as parameter

            // 2. Find distinct relevant ActivityInstance Roots linked via groupings
            MATCH (activity_value)-[:HAS_GROUPING]->(:ActivityGrouping)<-[:HAS_ACTIVITY]-(:ActivityInstanceValue)<-[aihv_check:HAS_VERSION]-(ai_root:ActivityInstanceRoot)
            // *** NOTE: Add appropriate deletion check here if needed ***
            WHERE aihv_check.start_date <= version_end_date
            WITH DISTINCT ai_root, version_end_date
{pagination_clause}
            WITH ai_root, version_end_date // Pass paginated roots forward

            // --- Instance Detail Fetching ---

            // 4. For each paginated root, find all its versions
            MATCH (ai_root)-[aihv:HAS_VERSION]->(ai_val:ActivityInstanceValue)
            // *** NOTE: Add appropriate deletion check here if needed ***

            // 5. Filter versions active within the window & Order them
            WITH ai_root, aihv, ai_val, version_end_date
            WHERE aihv.start_date <= version_end_date
            WITH ai_root, aihv, ai_val, version_end_date // Pass rows for ordering
            ORDER BY ai_root.uid, aihv.start_date DESC, toFloat(aihv.version) DESC

            // 6. Collect the ordered versions per root
            WITH ai_root, version_end_date, collect({{rel: aihv, val: ai_val}}) as relevant_versions_sorted

            // 7. Identify the specific version to display (the first in the sorted list)
            // Use RETURN DISTINCT to handle potential duplicates if pagination wasn't perfect (shouldn't happen with ORDER BY uid)
            WITH DISTINCT ai_root, relevant_versions_sorted[0] as display_instance_map // Map {{rel:..., val:...}}

            // 8. Get library info for the root
            OPTIONAL MATCH (library)-[:CONTAINS_CONCEPT]->(ai_root)

            // 9. Get ActivityInstanceClass for the display instance version node
            WITH ai_root, display_instance_map, library, display_instance_map.val as display_instance_node
            OPTIONAL MATCH (display_instance_node)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)-[:LATEST]->(aic_value:ActivityInstanceClassValue)

            // 10. Find all *other* versions (children)
            WITH ai_root, display_instance_map, display_instance_node, library, aic_value
            OPTIONAL MATCH (ai_root)-[child_aihv:HAS_VERSION]->(child_ai_val:ActivityInstanceValue)
            WHERE child_aihv <> display_instance_map.rel AND
                  (child_aihv.start_date < display_instance_map.rel.start_date
                   OR (child_aihv.start_date = display_instance_map.rel.start_date AND toFloat(child_aihv.version) < toFloat(display_instance_map.rel.version)))
            // *** NOTE: Add appropriate deletion check here if needed ***

            // 11. Get ActivityInstanceClass for children
            OPTIONAL MATCH (child_ai_val)-[:ACTIVITY_INSTANCE_CLASS]->(:ActivityInstanceClassRoot)-[:LATEST]->(child_aic_value:ActivityInstanceClassValue)

            // 12. Order children (newest first) and collect
            WITH ai_root, display_instance_map, library, aic_value, child_aihv, child_ai_val, child_aic_value
            ORDER BY child_aihv.start_date DESC, toFloat(child_aihv.version) DESC
            WITH ai_root, display_instance_map, library, aic_value, collect(
                CASE WHEN child_aihv IS NULL THEN null ELSE {{
                    uid: ai_root.uid, version: child_aihv.version, status: child_aihv.status, name: child_ai_val.name,
                    definition: child_ai_val.definition, abbreviation: child_ai_val.abbreviation,
                    topic_code: child_ai_val.topic_code, adam_param_code: child_ai_val.adam_param_code,
                    activity_instance_class: CASE WHEN child_aic_value IS NULL THEN null ELSE {{ name: child_aic_value.name }} END
                }} END
            ) as children_data_list

            // 13. Format the final output map
            RETURN {{
                activity_instance_library_name: library.name, uid: ai_root.uid, version: display_instance_map.rel.version,
                status: display_instance_map.rel.status, name: display_instance_map.val.name,
                name_sentence_case: display_instance_map.val.name_sentence_case, abbreviation: display_instance_map.val.abbreviation,
                definition: display_instance_map.val.definition, adam_param_code: display_instance_map.val.adam_param_code,
                is_required_for_activity: coalesce(display_instance_map.val.is_required_for_activity, false),
                is_default_selected_for_activity: coalesce(display_instance_map.val.is_default_selected_for_activity, false),
                is_data_sharing: coalesce(display_instance_map.val.is_data_sharing, false),
                is_legacy_usage: coalesce(display_instance_map.val.is_legacy_usage, false),
                is_derived: coalesce(display_instance_map.val.is_derived, false),
                topic_code: display_instance_map.val.topic_code,
                activity_instance_class: CASE WHEN aic_value IS NULL THEN null ELSE {{ name: aic_value.name }} END,
                children: [c IN children_data_list WHERE c IS NOT NULL]
            }} AS instance
        """

        params_details = {
            "uid": activity_uid,
            "version": version,
            "version_end_date": version_end_date,
            # SKIP and LIMIT are embedded in the f-string, not passed as params here
        }

        try:
            instances_results, _ = db.cypher_query(
                query=details_query, params=params_details, resolve_objects=False
            )
            instances = [row[0] for row in instances_results]
        except Exception as e:
            # Log error or raise a more specific exception
            print(f"Error executing details query: {e}")
            raise  # Re-raise for now, or handle appropriately

        return instances, total_count
