from dataclasses import dataclass
from typing import AbstractSet

from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from common.exceptions import BusinessLogicException


@dataclass
class OdmARBase(ConceptARBase):
    _uid: str

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
            return {ObjectAction.REACTIVATE, ObjectAction.DELETE}
        return frozenset()

    def soft_delete(self) -> None:
        BusinessLogicException.raise_if(
            self._item_metadata.major_version != 0
            and self._item_metadata.status != LibraryItemStatus.RETIRED,
            msg="Object has been accepted or is not retired",
        )

        self._is_deleted = True
