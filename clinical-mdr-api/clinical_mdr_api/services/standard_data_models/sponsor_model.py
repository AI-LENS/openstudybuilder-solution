from clinical_mdr_api.domain_repositories.standard_data_models.sponsor_model_repository import (
    SponsorModelRepository,
)
from clinical_mdr_api.domains.standard_data_models.sponsor_model import (
    SponsorModelAR,
    SponsorModelVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.standard_data_models.sponsor_model import (
    SponsorModel,
    SponsorModelCreateInput,
    SponsorModelEditInput,
)
from clinical_mdr_api.services.neomodel_ext_generic import NeomodelExtGenericService


class SponsorModelService(NeomodelExtGenericService[SponsorModelAR]):
    repository_interface = SponsorModelRepository
    api_model_class = SponsorModel

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: SponsorModelAR
    ) -> SponsorModel:
        return SponsorModel.from_sponsor_model_ar(
            sponsor_model_ar=item_ar,
        )

    def _create_aggregate_root(
        self, item_input: SponsorModelCreateInput, library: LibraryVO
    ) -> SponsorModelAR:
        return SponsorModelAR.from_input_values(
            author_id=self.author_id,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=item_input.ig_uid,
                ig_version_number=item_input.ig_version_number,
                name=self.repository.generate_name(
                    ig_uid=item_input.ig_uid,
                    ig_version_number=item_input.ig_version_number,
                    version_number=item_input.version_number,
                ),
                version_number=item_input.version_number,
            ),
            library=library,
        )

    def _edit_aggregate(
        self, item: SponsorModelAR, item_edit_input: SponsorModelEditInput
    ) -> SponsorModelAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=item_edit_input.change_description,
            sponsor_model_vo=SponsorModelVO.from_repository_values(
                ig_uid=item_edit_input.ig_uid,
                ig_version_number=item_edit_input.ig_version_number,
                name=self.repository.generate_name(
                    ig_uid=item_edit_input.ig_uid,
                    ig_version_number=item_edit_input.ig_version_number,
                    version_number=item_edit_input.version_number,
                ),
                version_number=item_edit_input.version_number,
            ),
        )
        return item
