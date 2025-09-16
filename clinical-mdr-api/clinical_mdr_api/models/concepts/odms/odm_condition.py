from typing import Annotated, Callable, Self

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domains.concepts.odms.condition import OdmConditionAR
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domains.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
)
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.concepts.odms.odm_formal_expression import (
    OdmFormalExpressionBatchPatchInput,
    OdmFormalExpressionPostInput,
    OdmFormalExpressionSimpleModel,
)


class OdmCondition(ConceptModel):
    oid: Annotated[str | None, Field()]
    formal_expressions: Annotated[list[OdmFormalExpressionSimpleModel], Field()]
    descriptions: Annotated[list[OdmDescriptionSimpleModel], Field()]
    aliases: Annotated[list[OdmAliasSimpleModel], Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_condition_ar(
        cls,
        odm_condition_ar: OdmConditionAR,
        find_odm_formal_expression_by_uid: Callable[
            [str], OdmFormalExpressionAR | None
        ],
        find_odm_description_by_uid: Callable[[str], OdmDescriptionAR | None],
        find_odm_alias_by_uid: Callable[[str], OdmAliasAR | None],
    ) -> Self:
        return cls(
            uid=odm_condition_ar._uid,
            oid=odm_condition_ar.concept_vo.oid,
            name=odm_condition_ar.name,
            library_name=odm_condition_ar.library.name,
            start_date=odm_condition_ar.item_metadata.start_date,
            end_date=odm_condition_ar.item_metadata.end_date,
            status=odm_condition_ar.item_metadata.status.value,
            version=odm_condition_ar.item_metadata.version,
            change_description=odm_condition_ar.item_metadata.change_description,
            author_username=odm_condition_ar.item_metadata.author_username,
            formal_expressions=sorted(
                [
                    OdmFormalExpressionSimpleModel.from_odm_formal_expression_uid(
                        uid=formal_expression_uid,
                        find_odm_formal_expression_by_uid=find_odm_formal_expression_by_uid,
                    )
                    for formal_expression_uid in odm_condition_ar.concept_vo.formal_expression_uids
                ],
                key=lambda item: item.expression or "",
            ),
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_condition_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name or "",
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_condition_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name or "",
            ),
            possible_actions=sorted(
                [_.value for _ in odm_condition_ar.get_possible_actions()]
            ),
        )


class OdmConditionPostInput(ConceptPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    formal_expressions: Annotated[list[OdmFormalExpressionPostInput | str], Field()]
    descriptions: Annotated[list[OdmDescriptionPostInput | str], Field()]
    alias_uids: Annotated[list[str], Field()]


class OdmConditionPatchInput(ConceptPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    formal_expressions: Annotated[
        list[OdmFormalExpressionBatchPatchInput | OdmFormalExpressionPostInput | str],
        Field(),
    ]
    descriptions: Annotated[
        list[OdmDescriptionBatchPatchInput | OdmDescriptionPostInput | str], Field()
    ]
    alias_uids: Annotated[list[str], Field()]


class OdmConditionVersion(OdmCondition):
    """
    Class for storing OdmCondition and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
