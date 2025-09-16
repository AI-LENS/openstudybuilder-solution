from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.odms.item_repository import (
    ItemRepository,
)
from clinical_mdr_api.domains.concepts.odms.item import OdmItemAR, OdmItemVO
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
from clinical_mdr_api.models.concepts.odms.odm_item import (
    OdmItem,
    OdmItemActivityPostInput,
    OdmItemPatchInput,
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
    OdmItemVersion,
)
from clinical_mdr_api.services._utils import get_input_or_new_value
from clinical_mdr_api.services.concepts.odms.odm_descriptions import (
    OdmDescriptionService,
)
from clinical_mdr_api.services.concepts.odms.odm_generic_service import (
    OdmGenericService,
)
from clinical_mdr_api.utils import normalize_string
from common.exceptions import BusinessLogicException, NotFoundException


class OdmItemService(OdmGenericService[OdmItemAR]):
    aggregate_class = OdmItemAR
    version_class = OdmItemVersion
    repository_interface = ItemRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmItemAR
    ) -> OdmItem:
        return OdmItem.from_odm_item_ar(
            odm_item_ar=item_ar,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
            find_unit_definition_by_uid=self._repos.unit_definition_repository.find_by_uid_2,
            find_unit_definition_with_item_relation_by_item_uid=self._repos.odm_item_repository.find_unit_definition_with_item_relation_by_item_uid,
            find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
            find_codelist_attribute_by_codelist_uid=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_term_with_item_relation_by_item_uid=self._repos.odm_item_repository.find_term_with_item_relation_by_item_uid,
            find_activity_by_uid=self._repos.activity_repository.find_by_uid_2,
            find_odm_vendor_element_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_element_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_vendor_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(
        self, concept_input: OdmItemPostInput, library
    ) -> OdmItemAR:
        return OdmItemAR.from_input_values(
            author_id=self.author_id,
            concept_vo=OdmItemVO.from_repository_values(
                oid=concept_input.oid,
                name=concept_input.name,
                prompt=concept_input.prompt,
                datatype=concept_input.datatype,
                length=concept_input.length,
                significant_digits=concept_input.significant_digits,
                sas_field_name=concept_input.sas_field_name,
                sds_var_name=concept_input.sds_var_name,
                origin=concept_input.origin,
                comment=concept_input.comment,
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_input.descriptions
                ],
                alias_uids=concept_input.alias_uids,
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in concept_input.unit_definitions
                ],
                codelist_uid=concept_input.codelist_uid,
                term_uids=[term.uid for term in concept_input.terms],
                activity_uid=None,
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_item_repository.odm_object_exists,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
            unit_definition_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            find_codelist_attribute_callback=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_all_terms_callback=self._repos.ct_term_name_repository.find_all,
        )

    def _edit_aggregate(
        self, item: OdmItemAR, concept_edit_input: OdmItemPatchInput
    ) -> OdmItemAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmItemVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                prompt=concept_edit_input.prompt,
                datatype=concept_edit_input.datatype,
                length=concept_edit_input.length,
                significant_digits=concept_edit_input.significant_digits,
                sas_field_name=concept_edit_input.sas_field_name,
                sds_var_name=concept_edit_input.sds_var_name,
                origin=concept_edit_input.origin,
                comment=concept_edit_input.comment,
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_edit_input.descriptions
                ],
                alias_uids=concept_edit_input.alias_uids,
                unit_definition_uids=[
                    unit_definition.uid
                    for unit_definition in concept_edit_input.unit_definitions
                ],
                codelist_uid=concept_edit_input.codelist_uid,
                term_uids=[term.uid for term in concept_edit_input.terms],
                activity_uid=None,
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            odm_object_exists_callback=self._repos.odm_item_repository.odm_object_exists,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
            unit_definition_exists_by_callback=self._repos.unit_definition_repository.exists_by,
            find_codelist_attribute_callback=self._repos.ct_codelist_attribute_repository.find_by_uid,
            find_all_terms_callback=self._repos.ct_term_name_repository.find_all,
        )
        return item

    @db.transaction
    def create_with_relations(self, concept_input: OdmItemPostInput) -> OdmItem:
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

        item = self.non_transactional_create(
            concept_input=OdmItemPostInput(
                library_name=concept_input.library_name,
                oid=get_input_or_new_value(concept_input.oid, "I.", concept_input.name),
                name=concept_input.name,
                prompt=concept_input.prompt,
                datatype=concept_input.datatype,
                length=concept_input.length,
                significant_digits=concept_input.significant_digits,
                sas_field_name=concept_input.sas_field_name,
                sds_var_name=concept_input.sds_var_name,
                origin=concept_input.origin,
                comment=concept_input.comment,
                descriptions=description_uids,
                alias_uids=concept_input.alias_uids,
                unit_definitions=concept_input.unit_definitions,
                codelist_uid=concept_input.codelist_uid,
                terms=concept_input.terms,
            ),
        )

        self._manage_terms(item.uid, concept_input.terms)
        self._manage_unit_definitions(item.uid, concept_input.unit_definitions)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(item.uid)
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmItemPatchInput
    ) -> OdmItem:
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

        self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmItemPatchInput(
                change_description=concept_edit_input.change_description,
                name=concept_edit_input.name,
                oid=concept_edit_input.oid,
                prompt=concept_edit_input.prompt,
                datatype=concept_edit_input.datatype,
                length=concept_edit_input.length,
                significant_digits=concept_edit_input.significant_digits,
                sas_field_name=concept_edit_input.sas_field_name,
                sds_var_name=concept_edit_input.sds_var_name,
                origin=concept_edit_input.origin,
                comment=concept_edit_input.comment,
                descriptions=description_uids,
                alias_uids=concept_edit_input.alias_uids,
                unit_definitions=concept_edit_input.unit_definitions,
                codelist_uid=concept_edit_input.codelist_uid,
                terms=concept_edit_input.terms,
            ),
        )

        self._manage_terms(uid, concept_edit_input.terms, True)
        self._manage_unit_definitions(uid, concept_edit_input.unit_definitions, True)

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_repository.find_by_uid_2(uid)
        )

    def _manage_terms(
        self,
        item_uid: str,
        input_terms: list[OdmItemTermRelationshipInput],
        for_update: bool = False,
    ):
        if for_update:
            self._repos.odm_item_repository.remove_relation(
                uid=item_uid,
                relation_uid=None,
                relationship_type=RelationType.TERM,
                disconnect_all=True,
            )

        (
            items,
            prop_names,
        ) = self._repos.ct_term_attributes_repository.get_term_attributes_by_term_uids(
            [term.uid for term in input_terms]
        )

        terms = [dict(zip(prop_names, item)) for item in items]

        for input_term in input_terms:
            self._repos.odm_item_repository.add_relation(
                uid=item_uid,
                relation_uid=input_term.uid,
                relationship_type=RelationType.TERM,
                parameters={
                    "mandatory": input_term.mandatory,
                    "order": input_term.order,
                    "display_text": (
                        input_term.display_text
                        if not any(
                            input_term.uid == term["term_uid"]
                            and input_term.display_text == term["nci_preferred_name"]
                            for term in terms
                        )
                        else None
                    ),
                },
            )

    def _manage_unit_definitions(
        self,
        item_uid: str,
        unit_definitions: list[OdmItemUnitDefinitionRelationshipInput],
        for_update: bool = False,
    ):
        if for_update:
            self._repos.odm_item_repository.remove_relation(
                uid=item_uid,
                relation_uid=None,
                relationship_type=RelationType.UNIT_DEFINITION,
                disconnect_all=True,
            )

        for unit_definition in unit_definitions:
            self._repos.odm_item_repository.add_relation(
                uid=item_uid,
                relation_uid=unit_definition.uid,
                relationship_type=RelationType.UNIT_DEFINITION,
                parameters={
                    "mandatory": unit_definition.mandatory,
                    "order": unit_definition.order,
                },
            )

    @db.transaction
    def add_activity(
        self,
        uid: str,
        odm_item_activity_post_input: OdmItemActivityPostInput,
        override: bool = False,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        BusinessLogicException.raise_if(
            odm_item_ar.concept_vo.activity_uid and not override,
            msg="Only one activity can be linked to an ODM Item",
        )

        if override:
            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ACTIVITY,
                disconnect_all=True,
            )

        self._repos.odm_item_repository.add_relation(
            uid=uid,
            relation_uid=odm_item_activity_post_input.uid,
            relationship_type=RelationType.ACTIVITY,
        )

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def add_vendor_elements(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorElementRelationPostInput],
        override: bool = False,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.are_elements_vendor_compatible(
            odm_vendor_relation_post_input, VendorElementCompatibleType.ITEM_DEF
        )

        if override:
            self.fail_if_non_present_vendor_elements_are_used_by_current_odm_element_attributes(
                odm_item_ar._concept_vo.vendor_element_attribute_uids,
                odm_vendor_relation_post_input,
            )

            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT,
                disconnect_all=True,
            )

        for vendor_element in odm_vendor_relation_post_input:
            self._repos.odm_item_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element.uid,
                relationship_type=RelationType.VENDOR_ELEMENT,
                parameters={
                    "value": vendor_element.value,
                },
            )

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def add_vendor_attributes(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorRelationPostInput],
        override: bool = False,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_relation_post_input,
            compatible_type=VendorAttributeCompatibleType.ITEM_DEF,
        )

        if override:
            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_attribute in odm_vendor_relation_post_input:
            self._repos.odm_item_repository.add_relation(
                uid=uid,
                relation_uid=vendor_attribute.uid,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                parameters={
                    "value": vendor_attribute.value,
                },
            )

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    @db.transaction
    def add_vendor_element_attributes(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorRelationPostInput],
        override: bool = False,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_relation_post_input,
            odm_item_ar.concept_vo.vendor_element_uids,
        )

        if override:
            self._repos.odm_item_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_element_attribute in odm_vendor_relation_post_input:
            self._repos.odm_item_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element_attribute.uid,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                parameters={
                    "value": vendor_element_attribute.value,
                },
            )

        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_ar)

    def manage_vendors(
        self,
        uid: str,
        odm_vendors_post_input: OdmVendorsPostInput,
    ) -> OdmItem:
        odm_item_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        self.pre_management(
            uid, odm_vendors_post_input, odm_item_ar, self._repos.odm_item_repository
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
            self._repos.odm_item_repository.exists_by("uid", uid, True),
            "ODM Item",
            uid,
        )

        return self._repos.odm_item_repository.get_active_relationships(
            uid, ["item_ref"]
        )

    @db.transaction
    def get_items_that_belongs_to_item_groups(self):
        return self._repos.odm_item_repository.get_if_has_relationship("item_ref")
