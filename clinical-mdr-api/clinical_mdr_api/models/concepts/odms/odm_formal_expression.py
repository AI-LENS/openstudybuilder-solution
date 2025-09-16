from typing import Annotated, Callable, Self, overload

from pydantic import Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
)
from clinical_mdr_api.models.concepts.concept import NoLibraryConceptModelNoName
from clinical_mdr_api.models.utils import (
    BaseModel,
    InputModel,
    PatchInputModel,
    PostInputModel,
)


class OdmFormalExpression(NoLibraryConceptModelNoName):
    library_name: Annotated[str, Field()]
    context: Annotated[str | None, Field()]
    expression: Annotated[str | None, Field()]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_formal_expression_ar(
        cls,
        odm_formal_expression_ar: OdmFormalExpressionAR,
    ) -> Self:
        return cls(
            uid=odm_formal_expression_ar._uid,
            context=odm_formal_expression_ar.concept_vo.context,
            expression=odm_formal_expression_ar.concept_vo.expression,
            library_name=odm_formal_expression_ar.library.name,
            start_date=odm_formal_expression_ar.item_metadata.start_date,
            end_date=odm_formal_expression_ar.item_metadata.end_date,
            status=odm_formal_expression_ar.item_metadata.status.value,
            version=odm_formal_expression_ar.item_metadata.version,
            change_description=odm_formal_expression_ar.item_metadata.change_description,
            author_username=odm_formal_expression_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in odm_formal_expression_ar.get_possible_actions()]
            ),
        )


class OdmFormalExpressionSimpleModel(BaseModel):
    @overload
    @classmethod
    def from_odm_formal_expression_uid(
        cls,
        uid: str,
        find_odm_formal_expression_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_formal_expression_uid(
        cls,
        uid: None,
        find_odm_formal_expression_by_uid: Callable[[str], ConceptARBase | None],
    ) -> None: ...
    @classmethod
    def from_odm_formal_expression_uid(
        cls,
        uid: str | None,
        find_odm_formal_expression_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self | None:
        simple_odm_formal_expression_model = None

        if uid is not None:
            odm_formal_expression = find_odm_formal_expression_by_uid(uid)

            if odm_formal_expression is not None:
                simple_odm_formal_expression_model = cls(
                    uid=uid,
                    context=odm_formal_expression.concept_vo.context,
                    expression=odm_formal_expression.concept_vo.expression,
                    version=odm_formal_expression.item_metadata.version,
                )
            else:
                simple_odm_formal_expression_model = cls(
                    uid=uid,
                    context="",
                    expression="",
                    version=None,
                )
        return simple_odm_formal_expression_model

    uid: Annotated[str, Field()]
    context: Annotated[str, Field()]
    expression: Annotated[str, Field()]
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class OdmFormalExpressionPostInput(PostInputModel):
    library_name: Annotated[str, Field(min_length=1)] = "Sponsor"
    context: Annotated[str, Field(min_length=1)]
    expression: Annotated[str, Field(min_length=1)]


class OdmFormalExpressionPatchInput(PatchInputModel):
    change_description: Annotated[str, Field(min_length=1)]
    context: Annotated[str, Field(min_length=1)]
    expression: Annotated[str, Field(min_length=1)]


class OdmFormalExpressionBatchPatchInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    change_description: Annotated[str, Field(min_length=1)]
    context: Annotated[str, Field(min_length=1)]
    expression: Annotated[str, Field(min_length=1)]


class OdmFormalExpressionVersion(OdmFormalExpression):
    """
    Class for storing OdmFormalExpression and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
