from dataclasses import dataclass
from typing import Any, Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from common.exceptions import AlreadyExistsException, BusinessLogicException
from common.utils import booltostr


@dataclass(frozen=True)
class OdmItemVO(ConceptVO):
    oid: str | None
    prompt: str | None
    datatype: str | None
    length: int | None
    significant_digits: int | None
    sas_field_name: str | None
    sds_var_name: str | None
    origin: str | None
    comment: str | None
    description_uids: list[str]
    alias_uids: list[str]
    unit_definition_uids: list[str]
    codelist_uid: str | None
    term_uids: list[str]
    activity_uid: str | None
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        prompt: str | None,
        datatype: str | None,
        length: int | None,
        significant_digits: int | None,
        sas_field_name: str | None,
        sds_var_name: str | None,
        origin: str | None,
        comment: str | None,
        description_uids: list[str],
        alias_uids: list[str],
        unit_definition_uids: list[str],
        codelist_uid: str | None,
        term_uids: list[str],
        activity_uid: str | None,
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            prompt=prompt,
            datatype=datatype,
            length=length,
            significant_digits=significant_digits,
            sas_field_name=sas_field_name,
            sds_var_name=sds_var_name,
            origin=origin,
            comment=comment,
            description_uids=description_uids,
            alias_uids=alias_uids,
            unit_definition_uids=unit_definition_uids,
            codelist_uid=codelist_uid,
            term_uids=term_uids,
            activity_uid=activity_uid,
            vendor_element_uids=vendor_element_uids,
            vendor_attribute_uids=vendor_attribute_uids,
            vendor_element_attribute_uids=vendor_element_attribute_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        odm_object_exists_callback: Callable,
        odm_description_exists_by_callback: Callable[[str, str, bool], bool],
        get_odm_description_parent_uids_callback: Callable[[list[str]], dict],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        unit_definition_exists_by_callback: Callable[[str, str, bool], bool],
        find_codelist_attribute_callback: Callable[
            [str], CTCodelistAttributesAR | None
        ],
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ],
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        data = {
            "library_name": library_name,
            "alias_uids": self.alias_uids,
            "unit_definition_uids": self.unit_definition_uids,
            "codelist_uid": self.codelist_uid,
            "term_uids": self.term_uids,
            "name": self.name,
            "oid": self.oid,
            "datatype": self.datatype,
            "prompt": self.prompt,
            "length": self.length,
            "significant_digits": self.significant_digits,
            "sas_field_name": self.sas_field_name,
            "sds_var_name": self.sds_var_name,
            "origin": self.origin,
            "comment": self.comment,
        }
        if uids := odm_object_exists_callback(**data):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Item already exists with UID ({uids[0]}) and data {data}"
                )

        self.check_concepts_exist(
            [
                (
                    self.description_uids,
                    "ODM Description",
                    odm_description_exists_by_callback,
                ),
                (
                    self.alias_uids,
                    "ODM Alias",
                    odm_alias_exists_by_callback,
                ),
                (
                    self.unit_definition_uids,
                    "Unit Definition",
                    unit_definition_exists_by_callback,
                ),
            ],
            "ODM Item",
        )

        BusinessLogicException.raise_if(
            self.codelist_uid is not None
            and not find_codelist_attribute_callback(self.codelist_uid),
            msg=f"ODM Item tried to connect to non-existent Codelist with UID '{self.codelist_uid}'.",
        )

        if self.term_uids:
            BusinessLogicException.raise_if_not(
                self.codelist_uid,
                msg="To add terms you need to specify a codelist.",
            )

            codelist_term_uids = (
                [term.uid for term in find_all_terms_callback(self.codelist_uid).items]
                if self.codelist_uid is not None
                else []
            )
            for term_uid in self.term_uids:
                BusinessLogicException.raise_if(
                    term_uid not in codelist_term_uids,
                    msg=f"Term with UID '{term_uid}' doesn't belong to the specified Codelist with UID '{self.codelist_uid}'.",
                )

        if uids := get_odm_description_parent_uids_callback(self.description_uids):
            if odm_uid not in uids:
                raise BusinessLogicException(
                    msg=f"ODM Descriptions are already used: {dict(uids)}."
                )


@dataclass
class OdmItemAR(OdmARBase):
    _concept_vo: OdmItemVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmItemVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: OdmItemVO) -> None:
        self._concept_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmItemVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        return cls(
            _uid=uid,
            _concept_vo=concept_vo,
            _library=library,
            _item_metadata=item_metadata,
        )

    @classmethod
    def from_input_values(
        cls,
        author_id: str,
        concept_vo: OdmItemVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        get_odm_description_parent_uids_callback: Callable[
            [list[str]], dict
        ] = lambda _: {},
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_codelist_attribute_callback: Callable[
            [str], CTCodelistAttributesAR | None
        ] = lambda _: None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ] = lambda _: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            get_odm_description_parent_uids_callback=get_odm_description_parent_uids_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
            library_name=library.name,
        )

        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _concept_vo=concept_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        concept_vo: OdmItemVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_object_exists_callback: Callable = lambda _: True,
        odm_description_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        get_odm_description_parent_uids_callback: Callable[
            [list[str]], dict
        ] = lambda _: {},
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        unit_definition_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        find_codelist_attribute_callback: Callable[
            ..., CTCodelistAttributesAR | None
        ] = lambda _: None,
        find_all_terms_callback: Callable[
            [str], GenericFilteringReturn[CTTermNameAR] | None
        ] = lambda _: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            get_odm_description_parent_uids_callback=get_odm_description_parent_uids_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            unit_definition_exists_by_callback=unit_definition_exists_by_callback,
            find_codelist_attribute_callback=find_codelist_attribute_callback,
            find_all_terms_callback=find_all_terms_callback,
            odm_uid=self.uid,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmItemRefVO:
    uid: str
    oid: str
    name: str
    item_group_uid: str
    order_number: int
    mandatory: str
    key_sequence: str
    method_oid: str
    imputation_method_oid: str
    role: str
    role_codelist_oid: str
    collection_exception_condition_oid: str | None
    vendor: dict[Any, Any]

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        oid: str,
        name: str,
        item_group_uid: str,
        order_number: int,
        mandatory: bool,
        key_sequence: str,
        method_oid: str,
        imputation_method_oid: str,
        role: str,
        role_codelist_oid: str,
        vendor: dict[Any, Any],
        collection_exception_condition_oid: str | None = None,
    ) -> Self:
        return cls(
            uid=uid,
            oid=oid,
            name=name,
            item_group_uid=item_group_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            key_sequence=key_sequence,
            method_oid=method_oid,
            imputation_method_oid=imputation_method_oid,
            role=role,
            role_codelist_oid=role_codelist_oid,
            collection_exception_condition_oid=collection_exception_condition_oid,
            vendor=vendor,
        )


@dataclass(frozen=True)
class OdmItemTermVO:
    uid: str
    name: str
    mandatory: bool
    order: int
    display_text: str
    version: str

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        name: str,
        mandatory: bool,
        order: int,
        display_text: str,
        version: str,
    ) -> Self:
        return cls(
            uid=uid,
            name=name,
            mandatory=mandatory,
            order=order,
            display_text=display_text,
            version=version,
        )


@dataclass(frozen=True)
class OdmItemUnitDefinitionVO:
    uid: str
    name: str
    mandatory: bool
    order: int

    @classmethod
    def from_repository_values(
        cls, uid: str, name: str, mandatory: bool, order: int
    ) -> Self:
        return cls(uid=uid, name=name, mandatory=mandatory, order=order)
