from dataclasses import dataclass
from datetime import date
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException


@dataclass(frozen=True)
class OdmStudyEventVO(ConceptVO):
    oid: str | None
    effective_date: date | None
    retired_date: date | None
    description: str | None
    display_in_tree: bool
    form_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        name: str,
        oid: str | None,
        effective_date: date | None,
        retired_date: date | None,
        description: str | None,
        display_in_tree: bool,
        form_uids: list[str],
    ) -> Self:
        return cls(
            name=name,
            oid=oid,
            effective_date=effective_date,
            retired_date=retired_date,
            description=description,
            display_in_tree=display_in_tree,
            form_uids=form_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self, odm_object_exists_callback: Callable, odm_uid: str | None = None
    ) -> None:
        data = {
            "name": self.name,
            "oid": self.oid,
            "effective_date": (
                self.effective_date.strftime("%Y-%m-%d")
                if self.effective_date
                else None
            ),
            "retired_date": (
                self.retired_date.strftime("%Y-%m-%d") if self.retired_date else None
            ),
            "description": self.description,
            "display_in_tree": self.display_in_tree,
        }
        if uids := odm_object_exists_callback(**data):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Study Event already exists with UID ({uids[0]}) and data {data}"
                )


@dataclass
class OdmStudyEventAR(OdmARBase):
    _concept_vo: OdmStudyEventVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmStudyEventVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: OdmStudyEventVO) -> None:
        self._concept_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmStudyEventVO,
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
        concept_vo: OdmStudyEventVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        concept_vo.validate(odm_object_exists_callback=odm_object_exists_callback)

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
        concept_vo: OdmStudyEventVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_object_exists_callback: Callable = lambda _: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback, odm_uid=self.uid
        )

        if self._concept_vo != concept_vo:
            super()._edit_draft(
                change_description=change_description, author_id=author_id
            )
            self._concept_vo = concept_vo
