import datetime
from typing import Any, Iterable

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_repository import (
    ActivityRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity import (
    ActivityAR,
    ActivityGroupingVO,
    ActivityVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    Activity,
    ActivityCreateInput,
    ActivityEditInput,
    ActivityFromRequestInput,
    ActivityGrouping,
    ActivityOverview,
    ActivityRequestRejectInput,
    ActivityVersion,
    ActivityVersionDetail,
    CompactActivity,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstanceDetail,
    ActivityInstanceEditInput,
    ActivityInstanceGrouping,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services._utils import is_library_editable
from clinical_mdr_api.services.concepts import constants
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
    _AggregateRootType,
)
from clinical_mdr_api.utils import normalize_string
from common.config import settings
from common.exceptions import BusinessLogicException, NotFoundException


class ActivityService(ConceptGenericService[ActivityAR]):
    aggregate_class = ActivityAR
    version_class = ActivityVersion
    repository_interface = ActivityRepository

    def _transform_aggregate_root_to_pydantic_model(
        self,
        item_ar: ActivityAR,
    ) -> Activity:
        return Activity.from_activity_ar(activity_ar=item_ar)

    def _get_activity_groups_and_subgroups_from_activity_groupings(
        self, activity_groupings: Iterable[ActivityGrouping | ActivityGroupingVO]
    ) -> tuple[dict[str, _AggregateRootType], dict[str, _AggregateRootType]]:
        """Returns activity groups and subgroups from db by uids from activity groupings"""

        activity_group_uids = set()
        activity_subgroup_uids = set()

        for activity_grouping in activity_groupings:
            activity_group_uids.add(activity_grouping.activity_group_uid)
            activity_subgroup_uids.add(activity_grouping.activity_subgroup_uid)

        if activity_group_uids:
            activity_groups_by_uid = (
                self._repos.activity_group_repository.get_all_by_uid(
                    activity_group_uids,
                    get_latest_final=True,
                )
            )
        else:
            activity_groups_by_uid = {}

        if activity_subgroup_uids:
            activity_subgroups_by_uid = (
                self._repos.activity_subgroup_repository.get_all_by_uid(
                    activity_subgroup_uids,
                    get_latest_final=True,
                )
            )
        else:
            activity_subgroups_by_uid = {}

        return activity_groups_by_uid, activity_subgroups_by_uid

    @staticmethod
    def _to_activity_grouping_vo(
        activity_grouping: ActivityGrouping | ActivityGroupingVO,
        activity_groups_by_uid=tuple(),
        activity_subgroups_by_uid=tuple(),
    ) -> ActivityGroupingVO:
        return ActivityGroupingVO(
            activity_group_uid=activity_grouping.activity_group_uid,
            activity_group_name=(
                activity_groups_by_uid[activity_grouping.activity_group_uid].name
                if activity_grouping.activity_group_uid in activity_groups_by_uid
                else None
            ),
            activity_subgroup_uid=activity_grouping.activity_subgroup_uid,
            activity_subgroup_name=(
                activity_subgroups_by_uid[activity_grouping.activity_subgroup_uid].name
                if activity_grouping.activity_subgroup_uid in activity_subgroups_by_uid
                else None
            ),
        )

    def _to_activity_grouping_vos(
        self,
        activity_groupings: Iterable[ActivityGrouping | ActivityGroupingVO],
    ) -> list[ActivityGroupingVO]:
        acg_and_acsg_by_uid: tuple[Any, ...] = (
            self._get_activity_groups_and_subgroups_from_activity_groupings(
                activity_groupings
            )
        )
        activity_groups_by_uid: dict[Any, Any] = acg_and_acsg_by_uid[0]
        activity_subgroups_by_uid: dict[Any, Any] = acg_and_acsg_by_uid[1]
        return [
            self._to_activity_grouping_vo(
                activity_grouping,
                activity_groups_by_uid,
                activity_subgroups_by_uid,
            )
            for activity_grouping in activity_groupings
        ]

    def _create_aggregate_root(
        self,
        concept_input: ActivityCreateInput | ActivityFromRequestInput,
        library: LibraryVO,
    ) -> ActivityAR:
        # resolve names of activity groupings
        activity_groupings = (
            self._to_activity_grouping_vos(concept_input.activity_groupings)
            if concept_input.activity_groupings
            else []
        )

        return ActivityAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_input.nci_concept_id,
                nci_concept_name=concept_input.nci_concept_name,
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                synonyms=concept_input.synonyms or [],
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=[],
                request_rationale=concept_input.request_rationale,
                is_request_final=concept_input.is_request_final,
                is_data_collected=concept_input.is_data_collected,
                is_multiple_selection_allowed=concept_input.is_multiple_selection_allowed,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            get_activity_uids_by_synonyms_callback=self._repos.activity_repository.get_activity_uids_by_synonyms,
        )

    def _edit_aggregate(
        self, item: ActivityAR, concept_edit_input: ActivityEditInput
    ) -> ActivityAR:
        activity_groups_by_uid: dict[Any, Any] | set
        activity_subgroups_by_uid: dict[Any, Any] | set

        if "activity_groupings" in concept_edit_input.model_fields_set:
            acg_and_acsg_by_uid: tuple[Any, ...] = (
                self._get_activity_groups_and_subgroups_from_activity_groupings(
                    concept_edit_input.activity_groupings or []
                )
            )
            activity_groups_by_uid = acg_and_acsg_by_uid[0]
            activity_subgroups_by_uid = acg_and_acsg_by_uid[1]
            activity_groupings = (
                [
                    self._to_activity_grouping_vo(
                        activity_grouping,
                        activity_groups_by_uid,
                        activity_subgroups_by_uid,
                    )
                    for activity_grouping in concept_edit_input.activity_groupings
                ]
                if concept_edit_input.activity_groupings
                else []
            )
        else:
            activity_groupings = []
            activity_groups_by_uid = set()
            activity_subgroups_by_uid = set()
        synonyms = (
            [] if concept_edit_input.synonyms is None else concept_edit_input.synonyms
        )
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=concept_edit_input.nci_concept_id,
                nci_concept_name=concept_edit_input.nci_concept_name,
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                synonyms=synonyms,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_groupings=activity_groupings,
                activity_instances=[],
                request_rationale=concept_edit_input.request_rationale,
                is_request_final=concept_edit_input.is_request_final,
                is_data_collected=concept_edit_input.is_data_collected,
                is_multiple_selection_allowed=concept_edit_input.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=activity_subgroups_by_uid.__contains__,
            activity_group_exists=activity_groups_by_uid.__contains__,
            get_activity_uids_by_synonyms_callback=self._repos.activity_repository.get_activity_uids_by_synonyms,
        )
        return item

    @db.transaction
    def replace_requested_activity_with_sponsor(
        self, sponsor_activity_input: ActivityFromRequestInput
    ) -> Activity:
        NotFoundException.raise_if_not(
            self._repos.library_repository.library_exists(
                normalize_string(sponsor_activity_input.library_name)
            ),
            "Library",
            sponsor_activity_input.library_name,
            "Name",
        )

        library_vo = LibraryVO.from_input_values_2(
            library_name=sponsor_activity_input.library_name,
            is_library_editable_callback=is_library_editable,
        )

        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=sponsor_activity_input.activity_request_uid, for_update=True
        )
        NotFoundException.raise_if(
            activity_request_ar is None,
            "Requested Activity",
            sponsor_activity_input.activity_request_uid,
            "activity_request_uid",
        )
        BusinessLogicException.raise_if(
            activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL,
            msg=f"To update the Activity Request with Name '{activity_request_ar.name}' to Sponsor Activity it should be in Final state.",
        )
        activity_request_ar.inactivate(
            author_id=self.author_id,
            change_description="Inactivate Requested Activity as Sponsor Activity was created",
        )
        self.repository.save(activity_request_ar)

        concept_ar: ActivityAR = self._create_aggregate_root(
            concept_input=sponsor_activity_input, library=library_vo
        )
        concept_ar.approve(
            author_id=self.author_id,
            change_description="Approve Sponsor Activity created from Requested Activity",
        )
        self.repository.save(concept_ar)
        self.repository.replace_request_with_sponsor_activity(
            activity_request_uid=sponsor_activity_input.activity_request_uid,
            sponsor_activity_uid=concept_ar.uid,
        )
        return self._transform_aggregate_root_to_pydantic_model(concept_ar)

    @db.transaction
    def reject_activity_request(
        self,
        activity_request_uid: str,
        activity_request_rejection_input: ActivityRequestRejectInput,
    ) -> Activity:
        # retire Requested Activity first to not conflict the Sponsor Activity name
        activity_request_ar = self.repository.find_by_uid_2(
            uid=activity_request_uid, for_update=True
        )
        BusinessLogicException.raise_if_not(
            activity_request_ar,
            msg=f"The Activity Request with UID '{activity_request_uid}' doesn't exist.",
        )
        BusinessLogicException.raise_if(
            activity_request_ar.item_metadata.status != LibraryItemStatus.FINAL,
            msg=f"To reject Activity Request with Name '{activity_request_ar.name}' it has to be in Final state.",
        )
        BusinessLogicException.raise_if(
            activity_request_ar.library.name != settings.requested_library_name,
            msg="Only Requested Activities can be rejected.",
        )
        activity_request_ar.create_new_version(author_id=self.author_id)
        self.repository.save(activity_request_ar)
        activity_request_ar.edit_draft(
            author_id=self.author_id,
            change_description=f"Rejecting with the following reason {activity_request_rejection_input.reason_for_rejecting}",
            concept_vo=ActivityVO.from_repository_values(
                nci_concept_id=activity_request_ar.concept_vo.nci_concept_id,
                nci_concept_name=activity_request_ar.concept_vo.nci_concept_name,
                name=activity_request_ar.concept_vo.name,
                name_sentence_case=activity_request_ar.concept_vo.name_sentence_case,
                synonyms=activity_request_ar.concept_vo.synonyms,
                definition=activity_request_ar.concept_vo.definition,
                abbreviation=activity_request_ar.concept_vo.abbreviation,
                activity_groupings=activity_request_ar.concept_vo.activity_groupings,
                activity_instances=[],
                request_rationale=activity_request_ar.concept_vo.request_rationale,
                is_request_final=activity_request_ar.concept_vo.is_request_final,
                is_request_rejected=True,
                contact_person=activity_request_rejection_input.contact_person,
                reason_for_rejecting=activity_request_rejection_input.reason_for_rejecting,
                is_data_collected=activity_request_ar.concept_vo.is_data_collected,
                is_multiple_selection_allowed=activity_request_ar.concept_vo.is_multiple_selection_allowed,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_repository.latest_concept_in_library_exists_by_name,
            activity_subgroup_exists=self._repos.activity_subgroup_repository.final_concept_exists,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
            get_activity_uids_by_synonyms_callback=self._repos.activity_repository.get_activity_uids_by_synonyms,
        )
        self.repository.save(activity_request_ar)
        activity_request_ar.approve(
            author_id=self.author_id, change_description="Approving after rejecting"
        )
        self.repository.save(activity_request_ar)
        activity_request_ar.inactivate(
            author_id=self.author_id,
            change_description="Retiring rejected Activity Request",
        )
        self.repository.save(activity_request_ar)
        return self._transform_aggregate_root_to_pydantic_model(activity_request_ar)

    def get_activity_overview(
        self, activity_uid: str, version: str | None
    ) -> ActivityOverview:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_uid, True),
            "Activity",
            activity_uid,
        )

        overview = self._repos.activity_repository.get_activity_overview(
            uid=activity_uid, version=version
        )
        return ActivityOverview.from_repository_input(overview=overview)

    def get_cosmos_activity_overview(self, activity_uid: str) -> dict[str, Any]:
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_uid, True),
            "Activity",
            activity_uid,
        )

        data: dict[str, Any] = self.repository.get_cosmos_activity_overview(
            uid=activity_uid
        )
        result: dict[str, Any] = {
            "packageDate": datetime.date.today().isoformat(),
            "packageType": "bc",
            "conceptId": data["activity_value"]["nci_concept_id"],
            "ncitCode": data["activity_value"]["nci_concept_id"],
            "href": constants.COSM0S_BASE_ITEM_HREF.format(
                data["activity_value"]["nci_concept_id"]
            ),
            "categories": data["activity_subgroups"],
            "shortName": data["activity_value"]["name"],
            "synonyms": data["activity_value"]["abbreviation"],
            "resultScales": list(
                set(
                    constants.COSM0S_RESULT_SCALES_MAP.get(
                        instance["activity_instance_class_name"], ""
                    )
                    for instance in data["activity_instances"]
                )
            ),
            "definition": data["activity_value"]["definition"],
            "dataElementConcepts": [],
        }
        for activity_item in data["activity_items"]:
            result["dataElementConcepts"].append(
                {
                    "conceptId": activity_item["nci_concept_id"],
                    "ncitCode": activity_item["nci_concept_id"],
                    "href": constants.COSM0S_BASE_ITEM_HREF.format(
                        activity_item["nci_concept_id"]
                    ),
                    "shortName": activity_item["name"],
                    "dataType": constants.COSMOS_DEC_TYPES_MAP.get(
                        activity_item["type"], activity_item["type"]
                    ),
                    "exampleSet": activity_item["example_set"],
                }
            )
        return result

    def cascade_edit_and_approve(self, item: ActivityAR):
        if not item.concept_vo.is_data_collected:
            # Do not upversion any instances if the activity is without data collection
            return

        _, _, _, activity_after_save = item.repository_closure_data
        _, _, _, activity_before_save = activity_after_save.repository_closure_data
        item_metadata = activity_before_save.item_metadata
        last_final_version = f"{item_metadata.major_version}.0"

        linked_instances = (
            self._repos.activity_repository.get_linked_upgradable_activity_instances(
                uid=item.uid, version=last_final_version
            )
        )
        if linked_instances is None:
            return

        instance_service = ActivityInstanceService()

        for instance in linked_instances.get("activity_instances", []):
            if instance["version"]["status"] not in (
                LibraryItemStatus.DRAFT.value,
                LibraryItemStatus.FINAL.value,
            ):
                continue

            instance_groupings = []
            for grouping in item.concept_vo.activity_groupings:
                grp = {
                    "activity_uid": item.uid,
                    "activity_group_uid": grouping.activity_group_uid,
                    "activity_subgroup_uid": grouping.activity_subgroup_uid,
                }
                if grp in instance["activity_groupings"]:
                    instance_groupings.append(ActivityInstanceGrouping(**grp))

            if not instance_groupings:
                # No matching groupings found, skip this instance
                continue

            if instance["version"]["status"] == LibraryItemStatus.FINAL.value:
                instance_service.non_transactional_create_new_version(instance["uid"])

            # Edit all instances (both DRAFT and FINAL) to update their groupings
            edit_input = ActivityInstanceEditInput(
                change_description="Cascade edit",
                activity_groupings=instance_groupings,
                name=instance["name"],
                name_sentence_case=instance["name_sentence_case"],
            )
            instance_service.non_transactional_edit(
                uid=instance["uid"], concept_edit_input=edit_input, patch_mode=False
            )

            # Only approve instances that are in FINAL status
            if instance["version"]["status"] == LibraryItemStatus.FINAL.value:
                instance_service.non_transactional_approve(instance["uid"])

    def get_specific_activity_version_groupings(
        self,
        activity_uid: str,
        version: str,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> ActivityVersionDetail | GenericFilteringReturn[ActivityVersionDetail]:
        """
        Get activity groupings information for a specific version of an activity with pagination support.

        Args:
            activity_uid: The unique ID of the activity
            version: The version of the activity in format 'x.y'
            page_number: The page number for pagination
            page_size: The number of items per page
            total_count: Whether to include the total count of items

        Returns:
            A paginated response containing activity version details
        """
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_uid, True),
            "Activity",
            activity_uid,
        )

        data = self._repos.activity_repository.get_specific_activity_version_groupings(
            uid=activity_uid,
            version=version,
            page_number=page_number,
            page_size=page_size,
            total_count=total_count,
        )

        if isinstance(data, GenericFilteringReturn):
            # Handle paginated response from GenericFilteringReturn
            items = [
                ActivityVersionDetail.from_repository_input(item) for item in data.items
            ]
            return GenericFilteringReturn(items=items, total=data.total)

        # Handle non-paginated response for backward compatibility
        return ActivityVersionDetail.from_repository_input(data=data)

    def specific_version_exists(self, uid: str, version: str | None) -> bool:
        """Checks if a specific version exists for a given concept UID."""
        # This could be implemented in the repository if preferred, but here it's in the service
        query = """
            MATCH (root {uid: $uid})-[rel:HAS_VERSION {version: $version}]->()
            RETURN count(rel) > 0
        """
        # Ensure db is imported: from neomodel import db
        result, _ = db.cypher_query(query, params={"uid": uid, "version": version})
        return result[0][0] if result and result[0] else False

    def get_activity_instances_for_version(
        self,
        activity_uid: str,
        version: str | None,
        page_number: int = 1,
        page_size: int = 10,
    ) -> GenericFilteringReturn[ActivityInstanceDetail]:
        """
        Get activity instances relevant to a specific activity version's timeframe,
        with pagination.

        Args:
            activity_uid: The unique ID of the activity.
            version: The specific version of the activity (e.g., "16.0").
            page_number: The page number for pagination.
            page_size: The number of items per page.
        """
        NotFoundException.raise_if_not(
            self.repository.exists_by("uid", activity_uid, True),
            "Activity",
            activity_uid,
        )
        # Also check if the specific version exists for better error handling
        NotFoundException.raise_if_not(
            self.specific_version_exists(activity_uid, version),
            "Activity Version",
            f"{activity_uid} version {version}",
        )

        # Calculate skip value based on page number and size
        skip = (page_number - 1) * page_size if page_size > 0 else 0

        # Get instances and total count from repository
        instances, total_count = (
            self._repos.activity_repository.get_activity_instances_for_version(
                activity_uid=activity_uid,
                version=version,
                skip=skip,
                limit=page_size,
            )
        )

        # Transform each instance dict into a model
        instance_models = [ActivityInstanceDetail(**instance) for instance in instances]

        return GenericFilteringReturn(items=instance_models, total=total_count)

    def get_flattened_activity_instances_for_version(
        self,
        activity_uid: str,
        version: str | None,
        page_number: int = 1,
        page_size: int = 10,
    ) -> GenericFilteringReturn[ActivityInstanceDetail]:
        """
        Get flattened activity instances for export where parent and children are separate rows.

        Args:
            activity_uid: The unique ID of the activity.
            version: The specific version of the activity.
            page_number: The page number for pagination.
            page_size: The number of items per page (0 for all).

        Returns:
            A paginated response with flattened activity instances.
        """
        # Get all instances without pagination first
        result = self.get_activity_instances_for_version(
            activity_uid=activity_uid,
            version=version,
            page_number=1,
            page_size=0,  # Get all
        )

        # Flatten the parent-child hierarchy
        flattened_items = []
        for parent_instance in result.items:
            # Add the parent instance
            flattened_items.append(parent_instance)

            # Add all child versions as separate items
            if hasattr(parent_instance, "children") and parent_instance.children:
                for child in parent_instance.children:
                    # Convert child dict to ActivityInstanceDetail if needed
                    if isinstance(child, dict):
                        child_instance = ActivityInstanceDetail(**child)
                    else:
                        child_instance = child
                    flattened_items.append(child_instance)

        # Apply pagination to flattened list
        total = len(flattened_items)
        if page_size > 0:
            start_idx = (page_number - 1) * page_size
            end_idx = start_idx + page_size
            paginated_items = flattened_items[start_idx:end_idx]
        else:
            paginated_items = flattened_items

        return GenericFilteringReturn(items=paginated_items, total=total)

    def get_compact_activity_with_splitted_groupings(
        self,
        library: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[CompactActivity]:
        self.enforce_library(library)

        items, total = self.repository.get_compact_activity_with_splitted_groupings(
            library=library,
            total_count=total_count,
            sort_by=sort_by,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_number=page_number,
            page_size=page_size,
        )

        all_concepts = GenericFilteringReturn(items=items, total=total)
        all_concepts.items = [
            CompactActivity.from_repository_output(item) for item in all_concepts.items
        ]

        return all_concepts

    def get_compact_activity_with_splitted_groupings_distinct_values_for_header(
        self,
        library: str | None,
        field_name: str,
        search_string: str = "",
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        page_size: int = 10,
        **kwargs,
    ) -> list[Any]:
        self.enforce_library(library)

        header_values = self.repository.get_compact_activity_with_splitted_groupings_distinct_headers(
            library=library,
            field_name=field_name,
            search_string=search_string,
            filter_by=filter_by,
            filter_operator=filter_operator,
            page_size=page_size,
            **kwargs,
        )

        return header_values
