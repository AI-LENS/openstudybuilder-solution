from collections import defaultdict
from datetime import datetime
from typing import Callable, Iterable, Mapping

from fastapi import status
from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.activities.activity_instance_repository import (
    ActivityInstanceRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_activity_instance_repository import (
    SelectionHistory,
    StudySelectionActivityInstanceRepository,
)
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity import (
    StudySelectionActivityVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_activity_instance import (
    StudySelectionActivityInstanceAR,
    StudySelectionActivityInstanceVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityForStudyActivity,
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySelectionActivityInstance,
    StudySelectionActivityInstanceBatchCreate,
    StudySelectionActivityInstanceBatchOutput,
    StudySelectionActivityInstanceCreateInput,
    StudySelectionActivityInstanceEditInput,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.services._utils import (
    ensure_transaction,
    fill_missing_values_in_base_model_from_reference_base_model,
)
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.services.studies.study_activity_selection_base import (
    StudyActivitySelectionBaseService,
)
from common import exceptions
from common.auth.user import user


class StudyActivityInstanceSelectionService(StudyActivitySelectionBaseService):
    _repos: MetaRepository
    repository_interface = StudySelectionActivityInstanceRepository
    selected_object_repository_interface = ActivityInstanceRepository

    def update_dependent_objects(
        self,
        study_selection: StudySelectionActivityInstanceVO,
        previous_study_selection: StudySelectionActivityInstanceVO,
    ):
        pass

    def _find_ar_and_validate_new_order(
        self,
        study_uid: str,
        study_selection_uid: str,
        new_order: int,
    ):
        pass

    def _filter_ars_from_same_parent(
        self,
        selection_aggregate: StudySelectionActivityInstanceAR,
        selection_vo: StudySelectionActivityInstanceVO,
    ) -> StudySelectionActivityInstanceAR:
        return selection_aggregate

    _vo_to_ar_filter_map = {
        "order": "order",
        "start_date": "start_date",
        "author_id": "author_id",
        "activity.name": "activity_name",
        "activity_instance.name": "activity_instance_name",
        "study_soa_group.soa_group_term_name": "soa_group_term_name",
        "study_activity_subgroup.activity_subgroup_name": "activity_subgroup_name",
        "study_activity_group.activity_group_name": "activity_group_name",
    }

    def _get_selected_object_exist_check(self) -> Callable[[str], bool]:
        return self.selected_object_repository.final_concept_exists

    def _transform_from_vo_to_response_model(
        self,
        study_uid: str,
        specific_selection: StudySelectionActivityInstanceVO,
        terms_at_specific_datetime: datetime | None = None,
        accepted_version: bool = False,
        activity_versions_by_uid: (
            Mapping[str, Iterable[ActivityForStudyActivity]] | None
        ) = None,
        activity_instance_versions_by_uid: (
            Mapping[str, Iterable[ActivityInstance]] | None
        ) = None,
    ) -> StudySelectionActivityInstance:
        return StudySelectionActivityInstance.from_study_selection_activity_instance_vo_and_order(
            study_uid=study_uid,
            study_selection=specific_selection,
            get_activity_by_uid_callback=self._transform_latest_activity_model,
            get_activity_by_uid_version_callback=self._transform_activity_model,
            get_activity_instance_by_uid_callback=self._transform_latest_activity_instance_model,
            get_activity_instance_by_uid_version_callback=self._transform_activity_instance_model,
            activity_versions_by_uid=activity_versions_by_uid,
            activity_instance_versions_by_uid=activity_instance_versions_by_uid,
        )

    def _transform_all_to_response_model(
        self,
        study_selection: StudySelectionActivityInstanceAR,
        study_value_version: str | None = None,
    ) -> list[StudySelectionActivityInstance]:
        activity_versions_by_uid: dict[str, list[ActivityForStudyActivity]] = (
            defaultdict(list)
        )

        for activity in self._get_linked_activities(
            study_selection.study_objects_selection
        ):
            activity_versions_by_uid[activity.uid].append(
                ActivityForStudyActivity.from_activity_ar_objects(
                    activity,
                    activity_instance_ars=[
                        ActivityHierarchySimpleModel(**item)
                        for item in activity.concept_vo.activity_instances
                    ],
                )
            )

        activity_instance_versions_by_uid: dict[str, list[ActivityInstance]] = (
            defaultdict(list)
        )

        for activity_instance in self._get_linked_activity_instances(
            study_selection.study_objects_selection
        ):
            activity_instance_versions_by_uid[activity_instance.uid].append(
                ActivityInstance.from_activity_instance_ar_objects(
                    activity_instance_ar=activity_instance
                )
            )

        return [
            self._transform_from_vo_to_response_model(
                study_uid=specific_selection.study_uid,
                specific_selection=specific_selection,
                activity_versions_by_uid=activity_versions_by_uid,
                activity_instance_versions_by_uid=activity_instance_versions_by_uid,
            )
            for order, specific_selection in enumerate(
                study_selection.study_objects_selection, start=1
            )
        ]

    def _get_linked_activity_instances(
        self,
        selection_vos: Iterable[StudySelectionActivityInstanceVO],
    ) -> list[ActivityInstanceAR]:
        version_specific_uids = defaultdict(set)

        for selection_vo in selection_vos:
            if selection_vo.activity_instance_uid:
                version_specific_uids[selection_vo.activity_instance_uid].add(
                    selection_vo.activity_instance_version
                )
                version_specific_uids[selection_vo.activity_instance_uid].add("LATEST")

        if not version_specific_uids:
            return []

        return self._repos.activity_instance_repository.get_all_optimized(
            version_specific_uids=version_specific_uids
        )[0]

    def _transform_history_to_response_model(
        self, study_selection_history: list[SelectionHistory], study_uid: str
    ) -> list[StudySelectionActivityInstance]:
        result = []
        for history in study_selection_history:
            result.append(
                StudySelectionActivityInstance.from_study_selection_history(
                    study_selection_history=history,
                    study_uid=study_uid,
                    get_activity_by_uid_version_callback=self._transform_activity_model,
                    get_activity_instance_by_uid_version_callback=self._transform_activity_instance_model,
                )
            )
        return result

    def activity_instance_validation(
        self,
        activity_instance_uid: str,
        study_activity_selection: StudySelectionActivityVO,
        current_activity_instance_uid: str | None = None,
        current_activity_instance_version: str | None = None,
    ):
        activity_instance_service = ActivityInstanceService()

        # If ActivityInstance wasn't changed we should fetch it in the version it was selected by StudyActivityInstance
        if activity_instance_uid == current_activity_instance_uid:
            activity_instance_ar = activity_instance_service.repository.find_by_uid_2(
                activity_instance_uid,
                version=current_activity_instance_version,
            )
        else:
            activity_instance_ar = activity_instance_service.repository.find_by_uid_2(
                activity_instance_uid
            )

        exceptions.NotFoundException.raise_if_not(
            activity_instance_ar, "Activity Instance", activity_instance_uid
        )

        exceptions.NotFoundException.raise_if(
            activity_instance_ar.item_metadata.status
            in [
                LibraryItemStatus.DRAFT,
                LibraryItemStatus.RETIRED,
            ],
            msg=f"There is no approved Activity Instance with UID '{activity_instance_uid}'.",
        )

        related_activity_instances = self._repos.activity_instance_repository.get_all_activity_instances_for_activity_grouping(
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
        )
        linked_activity_instances = []
        for activity_instance in related_activity_instances:
            if activity_instance.uid not in linked_activity_instances:
                linked_activity_instances.append(activity_instance.uid)
        exceptions.BusinessLogicException.raise_if(
            activity_instance_uid not in linked_activity_instances,
            msg=f"Activity Instance with Name '{activity_instance_ar.name}' isn't linked with the Activity with Name '{study_activity_selection.activity_name}'.",
        )

        return activity_instance_ar

    def _create_value_object(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInstanceCreateInput,
        **kwargs,
    ):
        _, study_activity_selection, _ = self._get_specific_activity_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=selection_create_input.study_activity_uid,
        )
        if selection_create_input.activity_instance_uid:
            activity_instance_ar = self.activity_instance_validation(
                activity_instance_uid=selection_create_input.activity_instance_uid,
                study_activity_selection=study_activity_selection,
            )
        else:
            activity_instance_ar = None

        # create new VO to add
        new_selection = StudySelectionActivityInstanceVO.from_input_values(
            study_uid=study_uid,
            author_id=self.author,
            activity_instance_uid=(
                activity_instance_ar.uid if activity_instance_ar else None
            ),
            activity_instance_version=(
                activity_instance_ar.item_metadata.version
                if activity_instance_ar
                else None
            ),
            study_activity_uid=selection_create_input.study_activity_uid,
            activity_uid=study_activity_selection.activity_uid,
            activity_subgroup_uid=study_activity_selection.activity_subgroup_uid,
            activity_group_uid=study_activity_selection.activity_group_uid,
            generate_uid_callback=self.repository.generate_uid,
        )
        return new_selection

    @db.transaction
    def make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInstanceCreateInput,
    ) -> StudySelectionActivityInstance:
        return self.non_transactional_make_selection(
            study_uid=study_uid, selection_create_input=selection_create_input
        )

    def non_transactional_make_selection(
        self,
        study_uid: str,
        selection_create_input: StudySelectionActivityInstanceCreateInput,
    ) -> StudySelectionActivityInstance:
        repos = self._repos
        try:
            # create new VO to add
            study_activity_instance_selection = self._create_value_object(
                study_uid=study_uid,
                selection_create_input=selection_create_input,
            )
            # add VO to aggregate
            study_activity_instance_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            assert study_activity_instance_aggregate is not None
            study_activity_instance_aggregate.add_object_selection(
                study_activity_instance_selection,
                self.selected_object_repository.check_exists_final_version,
                self._repos.ct_term_name_repository.term_specific_exists_by_uid,
            )
            study_activity_instance_aggregate.validate()
            # sync with DB and save the update
            self.repository.save(study_activity_instance_aggregate, self.author)

            study_activity_instance_aggregate = self.repository.find_by_study(
                study_uid=study_uid, for_update=True
            )
            # Fetch the new selection which was just added
            (
                specific_selection,
                _,
            ) = study_activity_instance_aggregate.get_specific_object_selection(
                study_activity_instance_selection.study_selection_uid
            )

            # add the activity and return
            return self._transform_from_vo_to_response_model(
                study_uid=study_activity_instance_aggregate.study_uid,
                specific_selection=specific_selection,
            )
        finally:
            repos.close()

    @db.transaction
    def delete_selection(self, study_uid: str, study_selection_uid: str):
        repos = self._repos
        try:
            # Load aggregate
            selection_aggregate = (
                repos.study_activity_instance_repository.find_by_study(
                    study_uid=study_uid, for_update=True
                )
            )

            # remove the connection
            assert selection_aggregate is not None
            selection_aggregate.remove_object_selection(study_selection_uid)

            # sync with DB and save the update
            repos.study_activity_instance_repository.save(
                selection_aggregate, self.author
            )
        finally:
            repos.close()

    def _patch_prepare_new_value_object(
        self,
        request_object: StudySelectionActivityInstanceEditInput,
        current_object: StudySelectionActivityInstanceVO,
    ) -> StudySelectionActivityInstanceVO:
        # transform current to input model
        transformed_current = StudySelectionActivityInstanceEditInput(
            show_activity_instance_in_protocol_flowchart=current_object.show_activity_instance_in_protocol_flowchart,
            activity_instance_uid=current_object.activity_instance_uid,
            study_activity_uid=current_object.study_activity_uid,
            keep_old_version=current_object.keep_old_version,
        )

        # fill the missing from the inputs
        fill_missing_values_in_base_model_from_reference_base_model(
            base_model_with_missing_values=request_object,
            reference_base_model=transformed_current,
        )

        _, study_activity_selection, _ = self._get_specific_activity_selection_by_uids(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_activity_uid,
        )
        if request_object.activity_instance_uid:
            activity_instance_ar = self.activity_instance_validation(
                activity_instance_uid=request_object.activity_instance_uid,
                study_activity_selection=study_activity_selection,
                current_activity_instance_uid=current_object.activity_instance_uid,
                current_activity_instance_version=current_object.activity_instance_version,
            )
        else:
            activity_instance_ar = None

        return StudySelectionActivityInstanceVO.from_input_values(
            study_uid=current_object.study_uid,
            study_selection_uid=current_object.study_selection_uid,
            author_id=user().id(),
            author_username=user().username,
            activity_instance_uid=(
                activity_instance_ar.uid if activity_instance_ar else None
            ),
            activity_instance_version=(
                activity_instance_ar.item_metadata.version
                if activity_instance_ar
                else None
            ),
            activity_uid=current_object.activity_uid,
            activity_subgroup_uid=current_object.activity_subgroup_uid,
            activity_group_uid=current_object.activity_group_uid,
            activity_version=current_object.activity_version,
            study_activity_uid=current_object.study_activity_uid,
            show_activity_instance_in_protocol_flowchart=request_object.show_activity_instance_in_protocol_flowchart,
            keep_old_version=request_object.keep_old_version,
        )

    def get_specific_selection(
        self,
        study_uid: str,
        study_selection_uid: str,
        study_value_version: str | None = None,
    ) -> StudySelectionActivityInstance:
        (
            _,
            specific_selection,
            _,
        ) = self._get_specific_activity_instance_selection_by_uids(
            study_uid, study_selection_uid, study_value_version=study_value_version
        )
        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=specific_selection,
        )

    @db.transaction
    def update_selection_to_latest_version(
        self, study_uid: str, study_selection_uid: str
    ):
        (
            selection_ar,
            selection,
            _,
        ) = self._get_specific_activity_instance_selection_by_uids(
            study_uid=study_uid,
            study_selection_uid=study_selection_uid,
            for_update=True,
        )
        activity_instance_uid = selection.activity_instance_uid
        activity_instance_ar = self._repos.activity_instance_repository.find_by_uid_2(
            activity_instance_uid, for_update=True
        )
        if activity_instance_ar.item_metadata.status == LibraryItemStatus.DRAFT:
            activity_instance_ar.approve(self.author)
            self._repos.activity_instance_repository.save(activity_instance_ar)
        elif activity_instance_ar.item_metadata.status == LibraryItemStatus.RETIRED:
            raise exceptions.BusinessLogicException(
                msg="Cannot add retired activity instances as selection. Please reactivate."
            )
        new_selection: StudySelectionActivityInstanceVO = selection.update_version(
            activity_instance_version=activity_instance_ar.item_metadata.version
        )

        # When we sync to latest version it means we clear keep_old_version flag as user
        # decided to update to latest version
        new_selection = new_selection.update_keep_old_version(keep_old_version=False)

        selection_ar.update_selection(new_selection)
        self._repos.study_activity_instance_repository.save(selection_ar, self.author)

        return self._transform_from_vo_to_response_model(
            study_uid=study_uid,
            specific_selection=new_selection,
        )

    @ensure_transaction(db)
    def batch_create(
        self,
        study_uid: str,
        create_payload: StudySelectionActivityInstanceBatchCreate,
    ) -> list[StudySelectionActivityInstanceBatchOutput]:
        results = []
        study_activity_instance_aggregate = self.repository.find_by_study(
            study_uid=study_uid, for_update=True
        )
        selected_instances = {
            study_activity_instance.activity_instance_uid: study_activity_instance.study_selection_uid
            for study_activity_instance in study_activity_instance_aggregate.study_objects_selection
        }

        for activity_instance_uid in create_payload.activity_instance_uids:
            result = {}
            try:
                if activity_instance_uid not in selected_instances:
                    item = self.non_transactional_make_selection(
                        study_uid=study_uid,
                        selection_create_input=StudySelectionActivityInstanceCreateInput(
                            activity_instance_uid=activity_instance_uid,
                            study_activity_uid=create_payload.study_activity_uid,
                        ),
                    )
                    response_code = status.HTTP_201_CREATED
                else:
                    item = self.get_specific_selection(
                        study_uid=study_uid,
                        study_selection_uid=selected_instances[activity_instance_uid],
                    )
                    response_code = status.HTTP_200_OK
                result["response_code"] = response_code
                if item:
                    result["content"] = item.model_dump()
                results.append(StudySelectionActivityInstanceBatchOutput(**result))
            except exceptions.MDRApiBaseException as error:
                results.append(
                    StudySelectionActivityInstanceBatchOutput.model_construct(
                        response_code=error.status_code,
                        content=BatchErrorResponse(message=str(error)),
                    )
                )
        return results
