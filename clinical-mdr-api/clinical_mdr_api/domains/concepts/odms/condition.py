from dataclasses import dataclass
from typing import Callable, Self

from clinical_mdr_api.domains.concepts.concept_base import ConceptVO
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domains.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
)
from clinical_mdr_api.domains.concepts.odms.odm_ar_base import OdmARBase
from clinical_mdr_api.domains.concepts.utils import ENG_LANGUAGE
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import AlreadyExistsException, BusinessLogicException


@dataclass(frozen=True)
class OdmConditionVO(ConceptVO):
    oid: str | None
    formal_expression_uids: list[str]
    description_uids: list[str]
    alias_uids: list[str]

    @classmethod
    def from_repository_values(
        cls,
        oid: str | None,
        name: str,
        formal_expression_uids: list[str],
        description_uids: list[str],
        alias_uids: list[str],
    ) -> Self:
        return cls(
            oid=oid,
            name=name,
            formal_expression_uids=formal_expression_uids,
            description_uids=description_uids,
            alias_uids=alias_uids,
            name_sentence_case=None,
            definition=None,
            abbreviation=None,
            is_template_parameter=False,
        )

    def validate(
        self,
        odm_object_exists_callback: Callable,
        find_odm_formal_expression_callback: Callable[
            [str], OdmFormalExpressionAR | None
        ],
        find_odm_description_callback: Callable[[str], OdmDescriptionAR | None],
        get_odm_description_parent_uids_callback: Callable[[list[str]], dict],
        odm_alias_exists_by_callback: Callable[[str, str, bool], bool],
        previous_formal_expression_uids: list[str] | None = None,
        odm_uid: str | None = None,
        library_name: str | None = None,
    ) -> None:
        data = {
            "library_name": library_name,
            "alias_uids": self.alias_uids,
            "formal_expression_uids": self.formal_expression_uids,
            "name": self.name,
            "oid": self.oid,
        }
        if uids := odm_object_exists_callback(**data):
            if uids[0] != odm_uid:
                raise AlreadyExistsException(
                    msg=f"ODM Condition already exists with UID ({uids[0]}) and data {data}"
                )

        self.check_concepts_exist(
            [
                (
                    self.alias_uids,
                    "ODM Alias",
                    odm_alias_exists_by_callback,
                )
            ],
            "ODM Condition",
        )

        contexts = set()
        for formal_expression_uid in self.formal_expression_uids:
            formal_expression = find_odm_formal_expression_callback(
                formal_expression_uid
            )
            BusinessLogicException.raise_if_not(
                formal_expression,
                msg="ODM Condition tried to connect to non-existent concepts "
                f"""[('Concept Name: ODM Formal Expression', "uids: {{'{formal_expression_uid}'}}")].""",
            )
            BusinessLogicException.raise_if(
                formal_expression.concept_vo.context in contexts,
                msg=f"ODM Condition tried to connect to ODM Formal Expressions with same Context '{formal_expression.concept_vo.context}'.",
            )
            contexts.add(formal_expression.concept_vo.context)

            if previous_formal_expression_uids is None:
                continue
            for previous_formal_expression_uid in previous_formal_expression_uids:
                previous_formal_expression = find_odm_formal_expression_callback(
                    previous_formal_expression_uid
                )
                BusinessLogicException.raise_if(
                    formal_expression
                    and previous_formal_expression
                    and formal_expression.concept_vo.context
                    == previous_formal_expression.concept_vo.context
                    and formal_expression.uid != previous_formal_expression.uid,
                    msg=f"ODM Condition tried to connect to ODM Formal Expressions with same Context '{formal_expression.concept_vo.context}'.",
                )

        if uids := get_odm_description_parent_uids_callback(self.description_uids):
            if odm_uid not in uids:
                raise BusinessLogicException(
                    msg=f"ODM Descriptions are already used: {dict(uids)}."
                )

        descriptions = []
        for description_uid in self.description_uids:
            desc = find_odm_description_callback(description_uid)
            BusinessLogicException.raise_if_not(
                desc,
                msg="ODM Condition tried to connect to non-existent concepts "
                f"""[('Concept Name: ODM Description', "uids: {{'{description_uid}'}}")].""",
            )
            descriptions.append(desc)

        BusinessLogicException.raise_if_not(
            any(
                description.concept_vo.language == ENG_LANGUAGE
                for description in descriptions
            ),
            msg="An English ODM Description must be provided.",
        )


@dataclass
class OdmConditionAR(OdmARBase):
    _concept_vo: OdmConditionVO

    @property
    def name(self) -> str:
        return self._concept_vo.name

    @property
    def concept_vo(self) -> OdmConditionVO:
        return self._concept_vo

    @concept_vo.setter
    def concept_vo(self, value: OdmConditionVO) -> None:
        self._concept_vo = value

    @classmethod
    def from_repository_values(
        cls,
        uid: str,
        concept_vo: OdmConditionVO,
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
        concept_vo: OdmConditionVO,
        library: LibraryVO,
        generate_uid_callback: Callable[[], str] = lambda: "",
        odm_object_exists_callback: Callable = lambda _: True,
        find_odm_formal_expression_callback: Callable[
            [str], OdmFormalExpressionAR | None
        ] = lambda _: None,
        find_odm_description_callback: Callable[
            [str], OdmDescriptionAR | None
        ] = lambda _: None,
        get_odm_description_parent_uids_callback: Callable[
            [list[str]], dict
        ] = lambda _: {},
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> Self:
        item_metadata = LibraryItemMetadataVO.get_initial_item_metadata(
            author_id=author_id
        )

        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            find_odm_formal_expression_callback=find_odm_formal_expression_callback,
            find_odm_description_callback=find_odm_description_callback,
            get_odm_description_parent_uids_callback=get_odm_description_parent_uids_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
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
        concept_vo: OdmConditionVO,
        concept_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
        odm_object_exists_callback: Callable = lambda _: True,
        find_odm_formal_expression_callback: Callable[
            [str], OdmFormalExpressionAR | None
        ] = lambda _: None,
        find_odm_description_callback: Callable[
            [str], OdmDescriptionAR | None
        ] = lambda _: None,
        get_odm_description_parent_uids_callback: Callable[
            [list[str]], dict
        ] = lambda _: {},
        odm_alias_exists_by_callback: Callable[
            [str, str, bool], bool
        ] = lambda x, y, z: True,
    ) -> None:
        """
        Creates a new draft version for the object.
        """
        concept_vo.validate(
            odm_object_exists_callback=odm_object_exists_callback,
            find_odm_formal_expression_callback=find_odm_formal_expression_callback,
            find_odm_description_callback=find_odm_description_callback,
            get_odm_description_parent_uids_callback=get_odm_description_parent_uids_callback,
            odm_alias_exists_by_callback=odm_alias_exists_by_callback,
            previous_formal_expression_uids=self._concept_vo.formal_expression_uids,
            odm_uid=self.uid,
        )

        super()._edit_draft(change_description=change_description, author_id=author_id)
        self._concept_vo = concept_vo
