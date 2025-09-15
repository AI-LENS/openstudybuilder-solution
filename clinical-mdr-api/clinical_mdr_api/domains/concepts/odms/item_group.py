from dataclasses import dataclass
from typing import Any, Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException
from common.utils import booltostr


@dataclass(frozen=True)
class OdmItemGroupVO(ConceptVO):
    oid: str | None
    repeating: str | int | None
    is_reference_data: str | int | None
    sas_dataset_name: str | None
    origin: str | None
    purpose: str | None
    comment: str | None
    description_uids: list[str]
    alias_uids: list[str]
    sdtm_domain_uids: list[str]
    activity_subgroup_uids: list[str]
    item_uids: list[str]
    vendor_attribute_uids: list[str]
    vendor_element_uids: list[str]
    vendor_element_attribute_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        repeating: str | int | None,
        is_reference_data: str | int | None,
        sas_dataset_name: str | None,
        origin: str | None,
        purpose: str | None,
        comment: str | None,
        description_uids: list[str],
        alias_uids: list[str],
        sdtm_domain_uids: list[str],
        activity_subgroup_uids: list[str],
        item_uids: list[str],
        vendor_element_uids: list[str],
        vendor_attribute_uids: list[str],
        vendor_element_attribute_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            repeating=repeating,
            is_reference_data=is_reference_data,
            sas_dataset_name=sas_dataset_name,
            origin=origin,
            purpose=purpose,
            comment=comment,
            description_uids=description_uids,
            alias_uids=alias_uids,
            sdtm_domain_uids=sdtm_domain_uids,
            activity_subgroup_uids=activity_subgroup_uids,
            item_uids=item_uids,
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
        find_term_callback: Callable[[str], CTTermAttributesAR | None],
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        data = {
            "library_name": library_name,
            "alias_uids": self.alias_uids,
            "sdtm_domain_uids": self.sdtm_domain_uids,
            "name": self.name,
            "oid": self.oid,
            "repeating": bool(self.repeating),
            "is_reference_data": bool(self.is_reference_data),
            "sas_dataset_name": self.sas_dataset_name,
            "origin": self.origin,
            "purpose": self.purpose,
            "comment": self.comment,
        }
        if uids := odm_object_exists_callback(**data):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Item Group already exists with UID ({uids[0]}) and data {data}"
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
            ],
            "ODM Item Group",
        )

        for sdtm_domain_uid in self.sdtm_domain_uids:
            BusinessLogicException.raise_if_not(
                find_term_callback(sdtm_domain_uid),
                msg=f"ODM Item Group tried to connect to non-existent SDTM Domain with UID '{sdtm_domain_uid}'.",
            )

        if uids := get_odm_description_parent_uids_callback(self.description_uids):
            if odm_uid not in uids:
                raise BusinessLogicException(
                    msg=f"ODM Descriptions are already used: {dict(uids)}."
                )


@dataclass
class OdmItemGroupAR(OdmARBase):
    _concept_vo: OdmItemGroupVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmItemGroupVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: OdmItemGroupVO) -> None:
        self._concept_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmItemGroupVO,
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
        concept_vo: OdmItemGroupVO,
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
        find_term_callback: Callable[[str], CTTermAttributesAR | None] = lambda _: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            get_odm_description_parent_uids_callback=get_odm_description_parent_uids_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            find_term_callback=find_term_callback,
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
        concept_vo: OdmItemGroupVO,
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
        find_term_callback: Callable[[str], CTTermAttributesAR | None] = lambda _: None,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            odm_description_exists_by_callback=odm_description_exists_by_callback,
            get_odm_description_parent_uids_callback=get_odm_description_parent_uids_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            find_term_callback=find_term_callback,
            odm_uid=self.uid,
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo


@dataclass(frozen=True)
class OdmItemGroupRefVO:
    uid: str
    oid: str
    name: str
    form_uid: str
    order_number: int
    mandatory: str
    collection_exception_condition_oid: str | None
    vendor: dict[Any, Any]

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        oid: str,
        name: str,
        form_uid: str,
        order_number: int,
        mandatory: bool,
        vendor: dict[Any, Any],
        collection_exception_condition_oid: str | None = None,
    ) -> Self:
        return cls(
            uid=uid,
            oid=oid,
            name=name,
            form_uid=form_uid,
            order_number=order_number,
            mandatory=booltostr(mandatory),
            collection_exception_condition_oid=collection_exception_condition_oid,
            vendor=vendor,
        )
