from neomodel import db

from clinical_mdr_api.domain_repositories.biomedical_concepts.activity_instance_class_repository import (
    ActivityInstanceClassRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassEditInput,
    ActivityInstanceClassInput,
    ActivityInstanceClassMappingInput,
    ActivityInstanceClassVersion,
    ActivityInstanceClassWithDataset,
)
from clinical_mdr_api.services._utils import ensure_transaction
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService
from common.exceptions import BusinessLogicException, NotFoundException


class ActivityInstanceClassService(NeomodelExtGenericService[ActivityInstanceClassAR]):
    repository_interface = ActivityInstanceClassRepository
    api_model_class = ActivityInstanceClass
    version_class = ActivityInstanceClassVersion

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClass:
        return ActivityInstanceClass.from_activity_instance_class_ar(
            activity_instance_class_ar=item_ar,
            get_parent_class=self._repos.activity_instance_class_repository.get_parent_class,
        )

    def _create_aggregate_root(
        self, item_input: ActivityInstanceClassInput, library: LibraryVO
    ) -> ActivityInstanceClassAR:
        return ActivityInstanceClassAR.from_input_values(
            author_id=self.author_id,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_input.name or "",
                order=item_input.order,
                definition=item_input.definition,
                is_domain_specific=item_input.is_domain_specific,
                level=item_input.level,
                dataset_class_uid=item_input.dataset_class_uid,
                activity_item_classes=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
            dataset_class_exists_by_uid=self._repos.dataset_class_repository.find_by_uid,  # type: ignore[arg-type]
        )

    def _edit_aggregate(
        self,
        item: ActivityInstanceClassAR,
        item_edit_input: ActivityInstanceClassEditInput,
    ) -> ActivityInstanceClassAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=item_edit_input.name or item.activity_instance_class_vo.name,
                order=item_edit_input.order,
                definition=item_edit_input.definition,
                is_domain_specific=item_edit_input.is_domain_specific,
                level=item_edit_input.level,
                dataset_class_uid=item_edit_input.dataset_class_uid,
                activity_item_classes=[],
            ),
            activity_instance_class_exists_by_name_callback=self._repos.activity_instance_class_repository.check_exists_by_name,
            dataset_class_exists_by_uid=self._repos.dataset_class_repository.find_by_uid,  # type: ignore[arg-type]
        )
        return item

    def patch_mappings(
        self, uid: str, mapping_input: ActivityInstanceClassMappingInput
    ) -> ActivityInstanceClass:
        activity_instance_class = (
            self._repos.activity_instance_class_repository.find_by_uid(uid)
        )

        NotFoundException.raise_if_not(
            activity_instance_class, "Activity Instance Class", uid
        )

        try:
            self._repos.activity_instance_class_repository.patch_mappings(
                uid, mapping_input.dataset_class_uid
            )
        finally:
            self._repos.activity_instance_class_repository.close()

        return self.get_by_uid(uid)

    def get_mapped_datasets(
        self,
        activity_instance_class_uid: str | None = None,
        include_sponsor: bool = True,
    ) -> list[ActivityInstanceClassWithDataset]:
        mapped_datasets = (
            self._repos.activity_instance_class_repository.get_mapped_datasets(
                activity_instance_class_uid=activity_instance_class_uid,
                include_sponsor=include_sponsor,
            )
        )

        return mapped_datasets

    @ensure_transaction(db)
    def create(self, item_input: ActivityInstanceClassInput) -> ActivityInstanceClass:
        rs = super().create(item_input=item_input)

        self.update_parent(rs.uid, item_input.parent_uid)

        return self.get_by_uid(rs.uid)

    @ensure_transaction(db)
    def edit_draft(
        self, uid: str, item_edit_input: ActivityInstanceClassEditInput
    ) -> ActivityInstanceClass:
        self._find_by_uid_or_raise_not_found(uid=uid, for_update=False)

        self.update_parent(uid, item_edit_input.parent_uid)

        return super().edit_draft(uid=uid, item_edit_input=item_edit_input)

    @ensure_transaction(db)
    def update_parent(self, uid: str, parent_uid: str | None = None):
        BusinessLogicException.raise_if(
            parent_uid
            and not self._repos.activity_instance_class_repository.check_exists_final_version(
                parent_uid
            ),
            msg=f"Activity Instance Class tried to connect to non-existent or non-final Activity Instance Class with UID '{parent_uid}'.",
        )

        self._repos.activity_instance_class_repository.update_parent(parent_uid, uid)
