import logging
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_sub_group_repository import (
    ActivitySubGroupRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
    ActivitySubGroupVO,
    SimpleActivityGroupVO,
)
from clinical_mdr_api.models.concepts.activities.activity import SimpleActivity
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivityGroup,
    ActivitySubGroup,
    ActivitySubGroupCreateInput,
    ActivitySubGroupDetail,
    ActivitySubGroupEditInput,
    ActivitySubGroupOverview,
    ActivitySubGroupVersion,
)
from clinical_mdr_api.models.utils import CustomPage, GenericFilteringReturn
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.concept_generic_service import (
    ConceptGenericService,
)
from common import exceptions

logger = logging.getLogger(__name__)


class ActivitySubGroupService(ConceptGenericService[ActivitySubGroupAR]):
    aggregate_class = ActivitySubGroupAR
    repository_interface = ActivitySubGroupRepository
    version_class = ActivitySubGroupVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivitySubGroupAR
    ) -> ActivitySubGroup:
        return ActivitySubGroup.from_activity_ar(
            activity_subgroup_ar=item_ar,
            find_activity_by_uid=self._repos.activity_group_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: ActivitySubGroupCreateInput, library
    ) -> ActivitySubGroupAR:
        return ActivitySubGroupAR.from_input_values(
            author_id=self.author_id,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_input.name,
                name_sentence_case=concept_input.name_sentence_case,
                definition=concept_input.definition,
                abbreviation=concept_input.abbreviation,
                activity_groups=(
                    [
                        SimpleActivityGroupVO(activity_group_uid=activity_group)
                        for activity_group in concept_input.activity_groups
                    ]
                    if concept_input.activity_groups
                    else []
                ),
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            concept_exists_by_library_and_name_callback=self._repos.activity_subgroup_repository.latest_concept_in_library_exists_by_name,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )

    def _edit_aggregate(
        self,
        item: ActivitySubGroupAR,
        concept_edit_input: ActivitySubGroupEditInput,
    ) -> ActivitySubGroupAR:
        activity_groups = (
            [
                SimpleActivityGroupVO(activity_group_uid=activity_group)
                for activity_group in concept_edit_input.activity_groups
            ]
            if concept_edit_input.activity_groups
            else []
        )
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=ActivitySubGroupVO.from_repository_values(
                name=concept_edit_input.name,
                name_sentence_case=concept_edit_input.name_sentence_case,
                definition=concept_edit_input.definition,
                abbreviation=concept_edit_input.abbreviation,
                activity_groups=activity_groups,
            ),
            concept_exists_by_library_and_name_callback=self._repos.activity_subgroup_repository.latest_concept_in_library_exists_by_name,
            activity_group_exists=self._repos.activity_group_repository.final_concept_exists,
        )
        return item

    def get_subgroup_overview(
        self, subgroup_uid: str, version: str | None = None
    ) -> ActivitySubGroupOverview:
        subgroup = self.get_by_uid(subgroup_uid, version=version)
        # Get all versions and deduplicate by version number for the overview
        version_history = self.get_version_history(subgroup_uid)
        all_versions = []
        for version_item in version_history:
            if version_item.version not in all_versions:
                all_versions.append(version_item.version)

        # Get UIDs and versions of activity groups linked to this subgroup at this specific version point
        linked_activity_group_data = (
            self._repos.activity_subgroup_repository.get_linked_activity_group_uids(
                subgroup_uid=subgroup_uid, version=subgroup.version
            )
        )
        logger.debug(
            "Linked activity group data for subgroup %s version %s: %s",
            subgroup_uid,
            subgroup.version,
            linked_activity_group_data,
        )

        activity_groups: list[ActivityGroup] = []
        if linked_activity_group_data:
            # Dynamically import ActivityGroupService to avoid circular imports
            from clinical_mdr_api.services.concepts.activities.activity_group_service import (
                ActivityGroupService,
            )

            activity_group_service = ActivityGroupService()

            for group_data in linked_activity_group_data:
                try:
                    logger.debug(
                        "Fetching activity group with UID: %s and version: %s",
                        group_data["uid"],
                        group_data["version"],
                    )
                    activity_group = activity_group_service.get_by_uid(
                        uid=group_data["uid"], version=group_data["version"]
                    )
                    # Add the linked version to the activity group information
                    activity_groups.append(
                        ActivityGroup(
                            uid=activity_group.uid,
                            name=activity_group.name,
                            version=group_data[
                                "version"
                            ],  # Use the version from the relationship
                            status=activity_group.status,
                        )
                    )
                    logger.debug(
                        "Added activity group: %s with version %s",
                        activity_group,
                        group_data["version"],
                    )
                except exceptions.NotFoundException:
                    logger.debug(
                        "Activity group with UID '%s' not found - skipping",
                        group_data["uid"],
                    )
                    continue
                except exceptions.BusinessLogicException as e:
                    logger.info(
                        "Business logic prevented access to activity group '%s': %s",
                        group_data["uid"],
                        str(e),
                    )
                    continue
                except db.DatabaseError as e:
                    logger.warning(
                        "Database error retrieving activity group '%s': %s",
                        group_data["uid"],
                        str(e),
                    )
                    continue

        logger.debug("Final activity groups: %s", activity_groups)

        activity_subgroup_detail = ActivitySubGroupDetail(
            name=subgroup.name,
            name_sentence_case=subgroup.name_sentence_case,
            library_name=subgroup.library_name,
            definition=subgroup.definition,
            start_date=subgroup.start_date,
            end_date=subgroup.end_date,
            status=subgroup.status,
            version=subgroup.version,
            possible_actions=subgroup.possible_actions,
            change_description=subgroup.change_description,
            author_username=subgroup.author_username,
            activity_groups=activity_groups,
        )

        result = ActivitySubGroupOverview(
            activity_subgroup=activity_subgroup_detail,
            all_versions=all_versions,
        )
        logger.debug(
            "Created overview with %s activity groups",
            len(activity_subgroup_detail.activity_groups),
        )
        return result

    def get_activities_for_subgroup(
        self,
        subgroup_uid: str,
        version: str | None = None,
        search_string: str = "",
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> GenericFilteringReturn[SimpleActivity]:
        """
        Get activities linked to a specific activity subgroup version with pagination.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version, or None for latest
            search_string: Optional search string to filter activities by name or other fields
            page_number: The page number for pagination (starting from 1)
            page_size: The number of items per page
            total_count: Whether to calculate the total count

        Returns:
            GenericFilteringReturn containing SimpleActivity objects linked to the activity subgroup
        """
        # Get the specific version of the subgroup to ensure it exists
        subgroup_ar = self.get_by_uid(subgroup_uid, version=version)

        linked_activity_data = (
            self._repos.activity_subgroup_repository.get_linked_activity_uids(
                subgroup_uid=subgroup_uid,
                version=subgroup_ar.version,
                search_string=search_string,
                page_number=page_number,
                page_size=page_size,
                total_count=total_count,
            )
        )
        logger.debug(
            "Linked activity data for subgroup %s version %s",
            subgroup_uid,
            subgroup_ar.version,
        )

        activities: list[SimpleActivity] = []
        if linked_activity_data and "activities" in linked_activity_data:
            activity_service = ActivityService()
            for activity_info in linked_activity_data["activities"]:
                try:
                    activity = activity_service.get_by_uid(
                        uid=activity_info["uid"], version=activity_info["version"]
                    )
                    activities.append(activity)
                except exceptions.NotFoundException:
                    logger.debug(
                        "Activity with UID '%s' version '%s' not found - skipping",
                        activity_info["uid"],
                        activity_info["version"],
                    )
                    continue
                except exceptions.BusinessLogicException as e:
                    logger.info(
                        "Business logic prevented access to activity '%s' version '%s': %s",
                        activity_info["uid"],
                        activity_info["version"],
                        str(e),
                    )
                    continue
                except db.DatabaseError as e:
                    logger.warning(
                        "Database error retrieving activity '%s' version '%s': %s",
                        activity_info["uid"],
                        activity_info["version"],
                        str(e),
                    )
                    continue

        # Get total count from repository call if requested
        total_items = linked_activity_data.get("total", 0) if total_count else 0

        # Return directly without additional pagination as it's now handled at the repository level
        return GenericFilteringReturn(items=activities, total=total_items)

    def get_activity_groups_for_subgroup_paginated(
        self,
        subgroup_uid: str,
        version: str | None = None,
        page_number: int = 1,
        page_size: int = 10,
        total_count: bool = False,
    ) -> CustomPage[ActivityGroup]:
        """
        Get activity groups for a specific activity subgroup with pagination.

        Args:
            subgroup_uid: The UID of the activity subgroup
            version: Optional specific version, or None for latest
            page_number: The page number for pagination (starting from 1)
            page_size: The number of items per page (0 for all items)
            total_count: Whether to calculate the total count

        Returns:
            CustomPage containing paginated ActivityGroup objects
        """
        # Get the overview which contains all activity groups
        overview = self.get_subgroup_overview(
            subgroup_uid=subgroup_uid, version=version
        )
        activity_groups = overview.activity_subgroup.activity_groups

        # Handle pagination
        start_idx = (page_number - 1) * page_size
        end_idx = start_idx + page_size if page_size > 0 else len(activity_groups)
        paginated_groups = (
            activity_groups[start_idx:end_idx] if page_size > 0 else activity_groups
        )

        total = len(activity_groups) if total_count else 0

        return CustomPage(
            items=paginated_groups, total=total, page=page_number, size=page_size
        )

    def get_cosmos_subgroup_overview(self, subgroup_uid: str) -> dict[str, Any]:
        """Get a COSMoS compatible representation of a specific activity subgroup.

        Args:
            subgroup_uid: The UID of the activity subgroup

        Returns:
            A dictionary representation compatible with COSMoS format
        """
        try:
            # Get the subgroup overview data formatted for COSMoS
            return (
                self._repos.activity_subgroup_repository.get_cosmos_subgroup_overview(
                    subgroup_uid=subgroup_uid
                )
            )
        except exceptions.BusinessLogicException as e:
            # Rethrow with more context if needed
            raise exceptions.BusinessLogicException(
                f"Error getting COSMoS subgroup overview for {subgroup_uid}: {str(e)}"
            ) from e
