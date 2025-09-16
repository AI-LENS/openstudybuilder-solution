from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.odms.form_repository import (
    FormRepository,
)
from clinical_mdr_api.domains.concepts.odms.form import OdmFormAR, OdmFormVO
from clinical_mdr_api.domains.concepts.utils import (
    RelationType,
    VendorAttributeCompatibleType,
    VendorElementCompatibleType,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryItemStatus
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmVendorElementRelationPostInput,
    OdmVendorRelationPostInput,
    OdmVendorsPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescriptionBatchPatchInput,
)
from clinical_mdr_api.models.concepts.odms.odm_form import (
    OdmForm,
    OdmFormActivityGroupPostInput,
    OdmFormItemGroupPostInput,
    OdmFormPatchInput,
    OdmFormPostInput,
    OdmFormVersion,
)
from clinical_mdr_api.services._utils import get_input_or_new_value
from clinical_mdr_api.services.concepts.odms.odm_descriptions import (
    OdmDescriptionService,
)
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)
from clinical_mdr_api.utils import normalize_string, to_dict
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import strtobool


class OdmFormService(OdmGenericService[OdmFormAR]):
    aggregate_class = OdmFormAR
    version_class = OdmFormVersion
    repository_interface = FormRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmFormAR
    ) -> OdmForm:
        return OdmForm.from_odm_form_ar(
            odm_form_ar=item_ar,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
            find_activity_group_by_uid=self._repos.activity_group_repository.find_by_uid_2,
            find_odm_vendor_attribute_by_uid=self._repos.odm_vendor_attribute_repository.find_by_uid_2,
            find_odm_item_group_by_uid_with_form_relation=self._repos.odm_item_group_repository.find_by_uid_with_form_relation,
            find_odm_vendor_element_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_element_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_vendor_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(
        self, concept_input: OdmFormPostInput, library
    ) -> OdmFormAR:
        return OdmFormAR.from_input_values(
            author_id=self.author_id,
            concept_vo=OdmFormVO.from_repository_values(
                oid=concept_input.oid,
                name=concept_input.name,
                sdtm_version=concept_input.sdtm_version,
                repeating=strtobool(concept_input.repeating),
                scope_uid=concept_input.scope_uid,
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_input.descriptions
                ],
                alias_uids=concept_input.alias_uids,
                activity_group_uids=[],
                item_group_uids=[],
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_form_repository.odm_object_exists,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )

    def _edit_aggregate(
        self, item: OdmFormAR, concept_edit_input: OdmFormPatchInput
    ) -> OdmFormAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmFormVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                sdtm_version=concept_edit_input.sdtm_version,
                repeating=strtobool(concept_edit_input.repeating),
                scope_uid=concept_edit_input.scope_uid,
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_edit_input.descriptions
                ],
                alias_uids=concept_edit_input.alias_uids,
                activity_group_uids=[],
                item_group_uids=[],
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            odm_object_exists_callback=self._repos.odm_form_repository.odm_object_exists,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
        )
        return item

    @db.transaction
    def create_with_relations(self, concept_input: OdmFormPostInput) -> OdmForm:
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

        form = self.non_transactional_create(
            concept_input=OdmFormPostInput(
                library_name=concept_input.library_name,
                name=concept_input.name,
                sdtm_version=concept_input.sdtm_version,
                oid=get_input_or_new_value(concept_input.oid, "F.", concept_input.name),
                repeating=concept_input.repeating,
                scope_uid=concept_input.scope_uid,
                descriptions=description_uids,
                alias_uids=concept_input.alias_uids,
            )
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_form_repository.find_by_uid_2(form.uid)
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmFormPatchInput
    ) -> OdmForm:
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

        form = self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmFormPatchInput(
                change_description=concept_edit_input.change_description,
                name=concept_edit_input.name,
                sdtm_version=concept_edit_input.sdtm_version,
                oid=concept_edit_input.oid,
                repeating=concept_edit_input.repeating,
                scope_uid=concept_edit_input.scope_uid,
                descriptions=description_uids,
                alias_uids=concept_edit_input.alias_uids,
            ),
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_form_repository.find_by_uid_2(form.uid)
        )

    @db.transaction
    def add_activity_groups(
        self,
        uid: str,
        odm_form_activity_group_post_input: list[OdmFormActivityGroupPostInput],
        override: bool = False,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ACTIVITY_GROUP,
                disconnect_all=True,
            )

        for activity_group in odm_form_activity_group_post_input:
            self._repos.odm_form_repository.add_relation(
                uid=uid,
                relation_uid=activity_group.uid,
                relationship_type=RelationType.ACTIVITY_GROUP,
            )

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_item_groups(
        self,
        uid: str,
        odm_form_item_group_post_input: list[OdmFormItemGroupPostInput],
        override: bool = False,
    ) -> OdmForm:
        return self.non_transactional_add_item_groups(
            uid, odm_form_item_group_post_input, override
        )

    def non_transactional_add_item_groups(
        self,
        uid: str,
        odm_form_item_group_post_input: list[OdmFormItemGroupPostInput],
        override: bool = False,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ITEM_GROUP,
                disconnect_all=True,
            )

        vendor_attribute_patterns = self.get_regex_patterns_of_attributes(
            [
                attribute.uid
                for input_attribute in odm_form_item_group_post_input
                if input_attribute.vendor
                for attribute in input_attribute.vendor.attributes
            ]
        )
        self.are_attributes_vendor_compatible(
            [
                vendor_attribute
                for item_group in odm_form_item_group_post_input
                for vendor_attribute in item_group.vendor.attributes
            ],
            VendorAttributeCompatibleType.ITEM_GROUP_REF,
        )

        for item_group in odm_form_item_group_post_input:
            if item_group.vendor:
                self.can_connect_vendor_attributes(item_group.vendor.attributes)
                self.attribute_values_matches_their_regex(
                    item_group.vendor.attributes,
                    vendor_attribute_patterns,
                )

            self._repos.odm_form_repository.add_relation(
                uid=uid,
                relation_uid=item_group.uid,
                relationship_type=RelationType.ITEM_GROUP,
                parameters={
                    "order_number": item_group.order_number,
                    "mandatory": strtobool(item_group.mandatory),
                    "collection_exception_condition_oid": item_group.collection_exception_condition_oid,
                    "vendor": to_dict(item_group.vendor),
                },
            )

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_vendor_elements(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorElementRelationPostInput],
        override: bool = False,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.are_elements_vendor_compatible(
            odm_vendor_relation_post_input, VendorElementCompatibleType.FORM_DEF
        )

        if override:
            self.fail_if_non_present_vendor_elements_are_used_by_current_odm_element_attributes(
                odm_form_ar._concept_vo.vendor_element_attribute_uids,
                odm_vendor_relation_post_input,
            )

            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT,
                disconnect_all=True,
            )

        for vendor_element in odm_vendor_relation_post_input:
            self._repos.odm_form_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element.uid,
                relationship_type=RelationType.VENDOR_ELEMENT,
                parameters={
                    "value": vendor_element.value,
                },
            )

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_vendor_attributes(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorRelationPostInput],
        override: bool = False,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.fail_if_these_attributes_cannot_be_added(
            input_attributes=odm_vendor_relation_post_input,
            compatible_type=VendorAttributeCompatibleType.FORM_DEF,
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_attribute in odm_vendor_relation_post_input:
            self._repos.odm_form_repository.add_relation(
                uid=uid,
                relation_uid=vendor_attribute.uid,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                parameters={
                    "value": vendor_attribute.value,
                },
            )

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    @db.transaction
    def add_vendor_element_attributes(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorRelationPostInput],
        override: bool = False,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_form_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_relation_post_input,
            odm_form_ar.concept_vo.vendor_element_uids,
        )

        if override:
            self._repos.odm_form_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_element_attribute in odm_vendor_relation_post_input:
            self._repos.odm_form_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element_attribute.uid,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                parameters={
                    "value": vendor_element_attribute.value,
                },
            )

        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_form_ar)

    def manage_vendors(
        self,
        uid: str,
        odm_vendors_post_input: OdmVendorsPostInput,
    ) -> OdmForm:
        odm_form_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        self.pre_management(
            uid, odm_vendors_post_input, odm_form_ar, self._repos.odm_form_repository
        )
        self.add_vendor_elements(uid, odm_vendors_post_input.elements, True)
        self.add_vendor_element_attributes(
            uid, odm_vendors_post_input.element_attributes, True
        )
        self.add_vendor_attributes(uid, odm_vendors_post_input.attributes, True)

        return self.get_by_uid(uid)

    @db.transaction
    def get_active_relationships(self, uid: str):
        NotFoundException.raise_if_not(
            self._repos.odm_form_repository.exists_by("uid", uid, True),
            "ODM Form",
            uid,
        )

        return self._repos.odm_form_repository.get_active_relationships(
            uid, ["form_ref"]
        )

    @db.transaction
    def get_forms_that_belongs_to_study_event(self):
        return self._repos.odm_form_repository.get_if_has_relationship("form_ref")
