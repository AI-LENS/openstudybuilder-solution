from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.odms.method_repository import (
    MethodRepository,
)
from clinical_mdr_api.domains.concepts.odms.method import OdmMethodAR, OdmMethodVO
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescriptionBatchPatchInput,
)
from clinical_mdr_api.models.concepts.odms.odm_formal_expression import (
    OdmFormalExpressionBatchPatchInput,
)
from clinical_mdr_api.models.concepts.odms.odm_method import (
    OdmMethod,
    OdmMethodPatchInput,
    OdmMethodPostInput,
    OdmMethodVersion,
)
from clinical_mdr_api.services._utils import get_input_or_new_value
from clinical_mdr_api.services.concepts.odms.odm_descriptions import (
    OdmDescriptionService,
)
from clinical_mdr_api.services.concepts.odms.odm_formal_expressions import (
    OdmFormalExpressionService,
)
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)
from common.exceptions import NotFoundException


class OdmMethodService(OdmGenericService[OdmMethodAR]):
    aggregate_class = OdmMethodAR
    version_class = OdmMethodVersion
    repository_interface = MethodRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmMethodAR
    ) -> OdmMethod:
        return OdmMethod.from_odm_method_ar(
            odm_method_ar=item_ar,
            find_odm_formal_expression_by_uid=self._repos.odm_formal_expression_repository.find_by_uid_2,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
        )

    def _create_aggregate_root(
        self, concept_input: OdmMethodPostInput, library
    ) -> OdmMethodAR:
        return OdmMethodAR.from_input_values(
            author_id=self.author_id,
            concept_vo=OdmMethodVO.from_repository_values(
                oid=concept_input.oid,
                name=concept_input.name,
                method_type=concept_input.method_type,
                formal_expression_uids=[
                    (
                        formal_expression
                        if isinstance(formal_expression, str)
                        else formal_expression.uid
                    )
                    for formal_expression in concept_input.formal_expressions
                ],
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_input.descriptions
                ],
                alias_uids=concept_input.alias_uids,
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_method_repository.odm_object_exists,
            find_odm_formal_expression_callback=self._repos.odm_formal_expression_repository.find_by_uid_2,
            find_odm_description_callback=self._repos.odm_description_repository.find_by_uid_2,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )

    def _edit_aggregate(
        self, item: OdmMethodAR, concept_edit_input: OdmMethodPatchInput
    ) -> OdmMethodAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmMethodVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                method_type=concept_edit_input.method_type,
                formal_expression_uids=[
                    (
                        formal_expression
                        if isinstance(formal_expression, str)
                        else formal_expression.uid
                    )
                    for formal_expression in concept_edit_input.formal_expressions
                ],
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_edit_input.descriptions
                ],
                alias_uids=concept_edit_input.alias_uids,
            ),
            odm_object_exists_callback=self._repos.odm_method_repository.odm_object_exists,
            find_odm_formal_expression_callback=self._repos.odm_formal_expression_repository.find_by_uid_2,
            find_odm_description_callback=self._repos.odm_description_repository.find_by_uid_2,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )
        return item

    @db.transaction
    def create_with_relations(self, concept_input: OdmMethodPostInput) -> OdmMethod:
        description_uids = [
            (
                description
                if isinstance(description, str)
                else OdmDescriptionService()
                .non_transactional_create(concept_input=description)
                .uid
            )
            for description in concept_input.descriptions
        ]

        formal_expression_uids = [
            (
                formal_expression
                if isinstance(formal_expression, str)
                else OdmFormalExpressionService()
                .non_transactional_create(concept_input=formal_expression)
                .uid
            )
            for formal_expression in concept_input.formal_expressions
        ]

        method = self.non_transactional_create(
            concept_input=OdmMethodPostInput(
                library_name=concept_input.library_name,
                oid=get_input_or_new_value(concept_input.oid, "M.", concept_input.name),
                name=concept_input.name,
                method_type=concept_input.method_type,
                formal_expressions=formal_expression_uids,
                descriptions=description_uids,
                alias_uids=concept_input.alias_uids,
            )
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_method_repository.find_by_uid_2(method.uid)
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmMethodPatchInput
    ) -> OdmMethod:
        description_uids = [
            (
                description
                if isinstance(description, str)
                else (
                    OdmDescriptionService()
                    .non_transactional_edit(
                        uid=description.uid, concept_edit_input=description
                    )
                    .uid
                    if isinstance(description, OdmDescriptionBatchPatchInput)
                    else OdmDescriptionService()
                    .non_transactional_create(concept_input=description)
                    .uid
                )
            )
            for description in concept_edit_input.descriptions
        ]

        formal_expression_uids = [
            (
                formal_expression
                if isinstance(formal_expression, str)
                else (
                    OdmFormalExpressionService()
                    .non_transactional_edit(
                        uid=formal_expression.uid, concept_edit_input=formal_expression
                    )
                    .uid
                    if isinstance(formal_expression, OdmFormalExpressionBatchPatchInput)
                    else OdmFormalExpressionService()
                    .non_transactional_create(concept_input=formal_expression)
                    .uid
                )
            )
            for formal_expression in concept_edit_input.formal_expressions
        ]

        method = self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmMethodPatchInput(
                change_description=concept_edit_input.change_description,
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                method_type=concept_edit_input.method_type,
                formal_expressions=formal_expression_uids,
                descriptions=description_uids,
                alias_uids=concept_edit_input.alias_uids,
            ),
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_method_repository.find_by_uid_2(method.uid)
        )

    @db.transaction
    def soft_delete(self, uid: str, cascade_delete: bool = False):
        """
        Works exactly as the parent soft_delete method.
        However, after deleting the ODM Method, it also sets all method_oid that use this ODM Method to null.

        This method is temporary and should be removed when the database relationship between ODM Method and its reference nodes is ready.
        """
        method = self._find_by_uid_or_raise_not_found(uid, for_update=True)
        method.soft_delete()
        self.repository.save(method)

        if cascade_delete:
            self.cascade_delete(method)

        self._repos.odm_method_repository.set_all_method_oid_properties_to_null(
            method.concept_vo.oid
        )

    @db.transaction
    def get_active_relationships(self, uid: str):
        NotFoundException.raise_if_not(
            self._repos.odm_method_repository.exists_by("uid", uid, True),
            "ODM Method",
            uid,
        )

        return self._repos.odm_method_repository.get_active_relationships(uid, [])
