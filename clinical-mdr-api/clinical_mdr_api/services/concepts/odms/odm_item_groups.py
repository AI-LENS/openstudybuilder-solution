from neomodel import db

from clinical_mdr_api.domain_repositories.concepts.odms.item_group_repository import (
    ItemGroupRepository,
)
from clinical_mdr_api.domains.concepts.odms.item_group import (
    OdmItemGroupAR,
    OdmItemGroupVO,
)
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
from clinical_mdr_api.models.concepts.odms.odm_item_group import (
    OdmItemGroup,
    OdmItemGroupActivitySubGroupPostInput,
    OdmItemGroupItemPostInput,
    OdmItemGroupPatchInput,
    OdmItemGroupPostInput,
    OdmItemGroupVersion,
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


class OdmItemGroupService(OdmGenericService[OdmItemGroupAR]):
    aggregate_class = OdmItemGroupAR
    version_class = OdmItemGroupVersion
    repository_interface = ItemGroupRepository

    def _transform_aggregate_root_to_pydantic_model(
        self, item_ar: OdmItemGroupAR
    ) -> OdmItemGroup:
        return OdmItemGroup.from_odm_item_group_ar(
            odm_item_group_ar=item_ar,
            find_odm_description_by_uid=self._repos.odm_description_repository.find_by_uid_2,
            find_odm_alias_by_uid=self._repos.odm_alias_repository.find_by_uid_2,
            find_term_by_uid=self._repos.ct_term_attributes_repository.find_by_uid,
            find_activity_subgroup_by_uid=self._repos.activity_subgroup_repository.find_by_uid_2,
            find_odm_vendor_attribute_by_uid=self._repos.odm_vendor_attribute_repository.find_by_uid_2,
            find_odm_item_by_uid_with_item_group_relation=self._repos.odm_item_repository.find_by_uid_with_item_group_relation,
            find_odm_vendor_element_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_element_repository.find_by_uid_with_odm_element_relation
            ),
            find_odm_vendor_attribute_by_uid_with_odm_element_relation=(
                self._repos.odm_vendor_attribute_repository.find_by_uid_with_odm_element_relation
            ),
        )

    def _create_aggregate_root(
        self, concept_input: OdmItemGroupPostInput, library
    ) -> OdmItemGroupAR:
        return OdmItemGroupAR.from_input_values(
            author_id=self.author_id,
            concept_vo=OdmItemGroupVO.from_repository_values(
                oid=concept_input.oid,
                name=concept_input.name,
                repeating=strtobool(concept_input.repeating),
                is_reference_data=strtobool(concept_input.is_reference_data),
                sas_dataset_name=concept_input.sas_dataset_name,
                origin=concept_input.origin,
                purpose=concept_input.purpose,
                comment=concept_input.comment,
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_input.descriptions
                ],
                alias_uids=concept_input.alias_uids,
                sdtm_domain_uids=concept_input.sdtm_domain_uids,
                activity_subgroup_uids=[],
                item_uids=[],
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            library=library,
            generate_uid_callback=self.repository.generate_uid,
            odm_object_exists_callback=self._repos.odm_item_group_repository.odm_object_exists,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
        )

    def _edit_aggregate(
        self, item: OdmItemGroupAR, concept_edit_input: OdmItemGroupPatchInput
    ) -> OdmItemGroupAR:
        item.edit_draft(
            author_id=self.author_id,
            change_description=concept_edit_input.change_description,
            concept_vo=OdmItemGroupVO.from_repository_values(
                oid=concept_edit_input.oid,
                name=concept_edit_input.name,
                repeating=strtobool(concept_edit_input.repeating),
                is_reference_data=strtobool(concept_edit_input.is_reference_data),
                sas_dataset_name=concept_edit_input.sas_dataset_name,
                origin=concept_edit_input.origin,
                purpose=concept_edit_input.purpose,
                comment=concept_edit_input.comment,
                description_uids=[
                    description if isinstance(description, str) else description.uid
                    for description in concept_edit_input.descriptions
                ],
                alias_uids=concept_edit_input.alias_uids,
                sdtm_domain_uids=concept_edit_input.sdtm_domain_uids,
                activity_subgroup_uids=[],
                item_uids=[],
                vendor_element_uids=[],
                vendor_attribute_uids=[],
                vendor_element_attribute_uids=[],
            ),
            odm_object_exists_callback=self._repos.odm_item_group_repository.odm_object_exists,
            odm_description_exists_by_callback=self._repos.odm_description_repository.exists_by,
            get_odm_description_parent_uids_callback=self._repos.odm_description_repository.get_parent_uids,
            odm_alias_exists_by_callback=self._repos.odm_alias_repository.exists_by,
            find_term_callback=self._repos.ct_term_attributes_repository.find_by_uid,
        )
        return item

    @db.transaction
    def create_with_relations(
        self, concept_input: OdmItemGroupPostInput
    ) -> OdmItemGroup:
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

        item_group = self.non_transactional_create(
            concept_input=OdmItemGroupPostInput(
                library_name=concept_input.library_name,
                oid=get_input_or_new_value(concept_input.oid, "G.", concept_input.name),
                name=concept_input.name,
                repeating=concept_input.repeating,
                is_reference_data=concept_input.is_reference_data,
                sas_dataset_name=concept_input.sas_dataset_name,
                origin=concept_input.origin,
                purpose=concept_input.purpose,
                comment=concept_input.comment,
                descriptions=description_uids,
                alias_uids=concept_input.alias_uids,
                sdtm_domain_uids=concept_input.sdtm_domain_uids,
            )
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_group_repository.find_by_uid_2(item_group.uid)
        )

    @db.transaction
    def update_with_relations(
        self, uid: str, concept_edit_input: OdmItemGroupPatchInput
    ) -> OdmItemGroup:
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

        item_group = self.non_transactional_edit(
            uid=uid,
            concept_edit_input=OdmItemGroupPatchInput(
                change_description=concept_edit_input.change_description,
                name=concept_edit_input.name,
                oid=concept_edit_input.oid,
                repeating=concept_edit_input.repeating,
                is_reference_data=concept_edit_input.is_reference_data,
                sas_dataset_name=concept_edit_input.sas_dataset_name,
                origin=concept_edit_input.origin,
                purpose=concept_edit_input.purpose,
                comment=concept_edit_input.comment,
                descriptions=description_uids,
                alias_uids=concept_edit_input.alias_uids,
                sdtm_domain_uids=concept_edit_input.sdtm_domain_uids,
            ),
        )

        return self._transform_aggregate_root_to_pydantic_model(
            self._repos.odm_item_group_repository.find_by_uid_2(item_group.uid)
        )

    @db.transaction
    def add_activity_subgroups(
        self,
        uid: str,
        odm_item_group_activity_subgroup_post_input: list[
            OdmItemGroupActivitySubGroupPostInput
        ],
        override: bool = False,
    ) -> OdmItemGroup:
        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_group_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        if override:
            self._repos.odm_item_group_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ACTIVITY_SUB_GROUP,
                disconnect_all=True,
            )

        for activity_subgroup in odm_item_group_activity_subgroup_post_input:
            self._repos.odm_item_group_repository.add_relation(
                uid=uid,
                relation_uid=activity_subgroup.uid,
                relationship_type=RelationType.ACTIVITY_SUB_GROUP,
            )

        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_group_ar)

    @db.transaction
    def add_items(
        self,
        uid: str,
        odm_item_group_item_post_input: list[OdmItemGroupItemPostInput],
        override: bool = False,
    ) -> OdmItemGroup:
        return self.non_transactional_add_items(
            uid, odm_item_group_item_post_input, override
        )

    def non_transactional_add_items(
        self,
        uid: str,
        odm_item_group_item_post_input: list[OdmItemGroupItemPostInput],
        override: bool = False,
    ) -> OdmItemGroup:
        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_group_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        if override:
            self._repos.odm_item_group_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.ITEM,
                disconnect_all=True,
            )

        vendor_attribute_patterns = self.get_regex_patterns_of_attributes(
            [
                attribute.uid
                for input_attribute in odm_item_group_item_post_input
                if input_attribute.vendor
                for attribute in input_attribute.vendor.attributes
            ]
        )
        self.are_attributes_vendor_compatible(
            [
                vendor_attribute
                for item in odm_item_group_item_post_input
                for vendor_attribute in item.vendor.attributes
            ],
            VendorAttributeCompatibleType.ITEM_REF,
        )

        for item in odm_item_group_item_post_input:
            if item.vendor:
                self.can_connect_vendor_attributes(item.vendor.attributes)
                self.attribute_values_matches_their_regex(
                    item.vendor.attributes,
                    vendor_attribute_patterns,
                )

            self._repos.odm_item_group_repository.add_relation(
                uid=uid,
                relation_uid=item.uid,
                relationship_type=RelationType.ITEM,
                parameters={
                    "order_number": item.order_number,
                    "mandatory": strtobool(item.mandatory),
                    "key_sequence": item.key_sequence,
                    "method_oid": item.method_oid,
                    "imputation_method_oid": item.imputation_method_oid,
                    "role": item.role,
                    "role_codelist_oid": item.role_codelist_oid,
                    "collection_exception_condition_oid": item.collection_exception_condition_oid,
                    "vendor": to_dict(item.vendor),
                },
            )

        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_group_ar)

    @db.transaction
    def add_vendor_elements(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorElementRelationPostInput],
        override: bool = False,
    ) -> OdmItemGroup:
        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_group_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.are_elements_vendor_compatible(
            odm_vendor_relation_post_input, VendorElementCompatibleType.ITEM_DEF
        )

        if override:
            self.fail_if_non_present_vendor_elements_are_used_by_current_odm_element_attributes(
                odm_item_group_ar._concept_vo.vendor_element_attribute_uids,
                odm_vendor_relation_post_input,
            )

            self._repos.odm_item_group_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT,
                disconnect_all=True,
            )

        for vendor_element in odm_vendor_relation_post_input:
            self._repos.odm_item_group_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element.uid,
                relationship_type=RelationType.VENDOR_ELEMENT,
                parameters={
                    "value": vendor_element.value,
                },
            )

        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_group_ar)

    @db.transaction
    def add_vendor_attributes(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorRelationPostInput],
        override: bool = False,
    ) -> OdmItemGroup:
        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_group_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_relation_post_input,
            compatible_type=VendorAttributeCompatibleType.ITEM_GROUP_DEF,
        )

        if override:
            self._repos.odm_item_group_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_attribute in odm_vendor_relation_post_input:
            self._repos.odm_item_group_repository.add_relation(
                uid=uid,
                relation_uid=vendor_attribute.uid,
                relationship_type=RelationType.VENDOR_ATTRIBUTE,
                parameters={
                    "value": vendor_attribute.value,
                },
            )

        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_group_ar)

    @db.transaction
    def add_vendor_element_attributes(
        self,
        uid: str,
        odm_vendor_relation_post_input: list[OdmVendorRelationPostInput],
        override: bool = False,
    ) -> OdmItemGroup:
        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        BusinessLogicException.raise_if(
            odm_item_group_ar.item_metadata.status == LibraryItemStatus.RETIRED,
            msg=self.OBJECT_IS_INACTIVE,
        )

        self.fail_if_these_attributes_cannot_be_added(
            odm_vendor_relation_post_input,
            odm_item_group_ar.concept_vo.vendor_element_uids,
        )

        if override:
            self._repos.odm_item_group_repository.remove_relation(
                uid=uid,
                relation_uid=None,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                disconnect_all=True,
            )

        for vendor_element_attribute in odm_vendor_relation_post_input:
            self._repos.odm_item_group_repository.add_relation(
                uid=uid,
                relation_uid=vendor_element_attribute.uid,
                relationship_type=RelationType.VENDOR_ELEMENT_ATTRIBUTE,
                parameters={
                    "value": vendor_element_attribute.value,
                },
            )

        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        return self._transform_aggregate_root_to_pydantic_model(odm_item_group_ar)

    def manage_vendors(
        self,
        uid: str,
        odm_vendors_post_input: OdmVendorsPostInput,
    ) -> OdmItemGroup:
        odm_item_group_ar = self._find_by_uid_or_raise_not_found(normalize_string(uid))

        self.pre_management(
            uid,
            odm_vendors_post_input,
            odm_item_group_ar,
            self._repos.odm_item_group_repository,
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
            self._repos.odm_item_group_repository.exists_by("uid", uid, True),
            "ODM Item Group",
            uid,
        )

        return self._repos.odm_item_group_repository.get_active_relationships(
            uid, ["item_group_ref"]
        )

    @db.transaction
    def get_item_groups_that_belongs_to_form(self):
        return self._repos.odm_item_group_repository.get_if_has_relationship(
            "item_group_ref"
        )
