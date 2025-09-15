from dataclasses import dataclass
from datetime import datetime
from typing import AbstractSet, Callable, Self

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
class CTTermCodelistVO:
    codelist_uid: str
    order: int | None
    library_name: str | None = None


@dataclass(frozen=True)
class CTTermNameVO:
    """
    The CTTermNameVO acts as the value object for a single CTTerm name
    """

    name: str
    name_sentence_case: str
    catalogue_name: str
    codelists: list[CTTermCodelistVO]
    queried_effective_date: datetime | None = None
    date_conflict: bool = False

    @classmethod
    def from_repository_values(
        cls,
        codelists: list[CTTermCodelistVO],
        name: str,
        name_sentence_case: str,
        catalogue_name: str,
        queried_effective_date: datetime | None = None,
        date_conflict: bool = False,
    ) -> Self:
        ct_term_name_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            name=name,
            name_sentence_case=name_sentence_case,
            queried_effective_date=queried_effective_date,
            date_conflict=date_conflict,
        )

        return ct_term_name_vo

    @classmethod
    def from_input_values(
        cls,
        codelists: list[CTTermCodelistVO],
        name: str,
        name_sentence_case: str,
        catalogue_name: str,
        codelist_exists_callback: Callable[[str], bool],
        catalogue_exists_callback: Callable[[str], bool],
        term_exists_by_name_in_codelists_callback: Callable[
            [str, list[str]], bool
        ] = lambda x, y: False,
    ) -> Self:
        for codelist in codelists:
            ValidationException.raise_if_not(
                codelist_exists_callback(codelist.codelist_uid),
                msg=f"Codelist with UID '{ codelist.codelist_uid}' doesn't exist.",
            )
        BusinessLogicException.raise_if_not(
            catalogue_exists_callback(catalogue_name),
            msg=f"Catalogue with Name '{catalogue_name}' doesn't exist.",
        )
        AlreadyExistsException.raise_if(
            name
            and term_exists_by_name_in_codelists_callback(
                name, [codelist.codelist_uid for codelist in codelists]
            ),
            "CT Term Name",
            name,
            "Name",
        )

        ct_term_name_vo = cls(
            codelists=codelists,
            catalogue_name=catalogue_name,
            name=name,
            name_sentence_case=name_sentence_case,
        )

        return ct_term_name_vo

    def validate(
        self,
    ) -> None:
        ValidationException.raise_if(
            self.name_sentence_case.lower() != self.name.lower(),
            msg=f"{self.name_sentence_case} isn't an independent case version of {self.name}",
        )


@dataclass
class CTTermNameAR(LibraryItemAggregateRootBase):
    _ct_term_name_vo: CTTermNameVO

    @property
    def name(self) -> str:
        return self._ct_term_name_vo.name

    @property
    def ct_term_vo(self) -> CTTermNameVO:
        return self._ct_term_name_vo

    def _is_edit_allowed_in_non_editable_library(self) -> bool:
        return True

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        ct_term_name_vo: CTTermNameVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        ct_term_ar = cls(
            _uid=uid,
            _ct_term_name_vo=ct_term_name_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return ct_term_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        ct_term_name_vo: CTTermNameVO,
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
            _ct_term_name_vo=ct_term_name_vo,
        )

    def edit_draft(
        self,
        author_id: str,
        change_description: str,
        ct_term_vo: CTTermNameVO,
        term_exists_by_name_in_codelists_callback: Callable[[str, list[str]], bool],
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        AlreadyExistsException.raise_if(
            ct_term_vo.name
            and term_exists_by_name_in_codelists_callback(
                ct_term_vo.name,
                [codelist.codelist_uid for codelist in self.ct_term_vo.codelists],
            )
            and self.ct_term_vo.name != ct_term_vo.name,
            "CT Term Name",
            ct_term_vo.name,
            "Name",
        )
        ct_term_vo.validate()
        if self._ct_term_name_vo != ct_term_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._ct_term_name_vo = ct_term_vo

    def create_new_version(self, author_id: str) -> None:
        """
        Puts object into DRAFT status with relevant changes to version numbers.
        """
        super()._create_new_version(author_id=author_id)

    def get_possible_actions(self) -> AbstractSet[ObjectAction]:
        """
        Returns list of possible actions
        """
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

    def set_new_order(
        self, codelist_uid: str, new_order: int, codelist_library_name: str
    ) -> None:
        ct_term_vo = CTTermNameVO.from_input_values(
            codelists=[
                CTTermCodelistVO(
                    codelist_uid=codelist_uid,
                    order=new_order,
                    library_name=codelist_library_name,
                )
            ],
            catalogue_name=self.ct_term_vo.catalogue_name,
            name=self.name,
            name_sentence_case=self.ct_term_vo.name_sentence_case,
            # passing always True callbacks, as we can't change catalogue
            # in scope of CTTermName or CTTermAttributes, it can be only changed via CTTermRoot
            codelist_exists_callback=lambda _: True,
            catalogue_exists_callback=lambda _: True,
        )
        self._ct_term_name_vo = ct_term_vo
