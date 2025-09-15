from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet, Callable, Self

from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
    ObjectAction,
)
from common.exceptions import (
    AlreadyExistsException,
    BusinessLogicException,
    ValidationException,
)


@dataclass(frozen=True)
class CTTermAttributesVO:
    """
    The CTTermAttributesVO acts as the value object for a single CTTerm attribute
    """

    codelists: list[CTTermCodelistVO]
    catalogue_name: str
    concept_id: str | None
    code_submission_value: str | None
    name_submission_value: str | None
    preferred_term: str | None
    definition: str

    @classmethod
    def from_repository_values(
        cls,
        codelists: list[CTTermCodelistVO],
        catalogue_name: str,
        concept_id: str | None,
        code_submission_value: str | None,
        name_submission_value: str | None,
        preferred_term: str | None,
        definition: str,
    ) -> Self:
        ct_term_attributes_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            concept_id=concept_id,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
        )
        return ct_term_attributes_vo

    @classmethod
    def from_input_values(
        cls,
        codelists: list[CTTermCodelistVO],
        catalogue_name: str,
        code_submission_value: str | None,
        name_submission_value: str | None,
        preferred_term: str | None,
        definition: str,
        codelist_exists_callback: Callable[[str], bool],
        catalogue_exists_callback: Callable[[str], bool],
        term_exists_by_name_callback: Callable[[str], bool] = lambda _: False,
        term_exists_by_code_submission_value_callback: Callable[
            [str], bool
        ] = lambda _: False,
    ) -> Self:
        for codelist in codelists:
            ValidationException.raise_if_not(
                codelist_exists_callback(codelist.codelist_uid),
                msg=f"Codelist with UID '{codelist.codelist_uid}' doesn't exist.",
            )

        ValidationException.raise_if_not(
            catalogue_exists_callback(catalogue_name),
            msg=f"Catalogue with Name '{catalogue_name}' doesn't exist.",
        )
        AlreadyExistsException.raise_if(
            name_submission_value
            and term_exists_by_name_callback(name_submission_value),
            "CT Term Attributes",
            name_submission_value,
            "Name",
        )
        AlreadyExistsException.raise_if(
            code_submission_value
            and term_exists_by_code_submission_value_callback(code_submission_value),
            "CT Term Attributes",
            code_submission_value,
            "Code Submission Value",
        )

        ct_term_attribute_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            concept_id=None,
            code_submission_value=code_submission_value,
            name_submission_value=name_submission_value,
            preferred_term=preferred_term,
            definition=definition,
        )
        return ct_term_attribute_vo


@dataclass
class CTTermAttributesAR(LibraryItemAggregateRootBase):
    _ct_term_attributes_vo: CTTermAttributesVO

    @property
    def name(self) -> str:
        return self._ct_term_attributes_vo.name_submission_value

    @property
    def ct_term_vo(self) -> CTTermAttributesVO:
        return self._ct_term_attributes_vo

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_attributes_vo: CTTermAttributesVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_attributes_vo=ct_term_attributes_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        ct_term_attributes_vo: CTTermAttributesVO,
        library: LibraryVO,
        start_date: datetime | None = None,
        generate_uid_callback: Callable[[], str | None] = lambda: None,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id, start_date=start_date
        )
        BusinessLogicException.raise_if_not(
            library.is_editable,
            msg=f"Library with Name '{library.name}' doesn't allow creation of objects.",
        )
        return cls(
            _uid=generate_uid_callback(),
            _item_metadata=item_metadata,
            _library=library,
            _ct_term_attributes_vo=ct_term_attributes_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        ct_term_vo: CTTermAttributesVO,
        term_exists_by_name_callback: Callable[[str], bool],
        term_exists_by_code_submission_value_callback: Callable[[str], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        AlreadyExistsException.raise_if(
            ct_term_vo.name_submission_value
            and term_exists_by_name_callback(ct_term_vo.name_submission_value)
            and self.ct_term_vo.name_submission_value
            != ct_term_vo.name_submission_value,
            "CT Term Attributes",
            ct_term_vo.name_submission_value,
            "Name",
        )
        AlreadyExistsException.raise_if(
            ct_term_vo.code_submission_value
            and term_exists_by_code_submission_value_callback(
                ct_term_vo.code_submission_value
            )
            and self.ct_term_vo.code_submission_value
            != ct_term_vo.code_submission_value,
            "CT Term Attributes",
            ct_term_vo.code_submission_value,
            "Code Submission Value",
        )

        if self._ct_term_attributes_vo != ct_term_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._ct_term_attributes_vo = ct_term_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
        if self.library.is_editable:
            if (
                self._item_metadata.status == LibraryItemStatus.DRAFT
                and self._item_metadata.major_version == 0
            ):
                return {ObjectAction.APPROVE, ObjectAction.EDIT, ObjectAction.DELETE}
            if self._item_metadata.status == LibraryItemStatus.DRAFT:
                return {ObjectAction.APPROVE, ObjectAction.EDIT}
            if self._item_metadata.status == LibraryItemStatus.FINAL:
                return {ObjectAction.NEWVERSION, ObjectAction.INACTIVATE}
            if self._item_metadata.status == LibraryItemStatus.RETIRED:
                return {ObjectAction.REACTIVATE}
        return frozenset()
