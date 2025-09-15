from typing import Annotated, Callable, Self, overload

from pydantic import Field, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.error import BatchErrorResponse
from clinical_mdr_api.models.utils import BaseModel, BatchInputModel
from clinical_mdr_api.models.validators import is_language_supported


class OdmDescription(ConceptModel):
    language: Annotated[str, Field()]
    description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    instruction: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    sponsor_instruction: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_description_ar(cls, odm_description_ar: OdmDescriptionAR) -> Self:
        return cls(
            uid=odm_description_ar._uid,
            name=odm_description_ar.name,
            language=odm_description_ar.concept_vo.language,
            description=odm_description_ar.concept_vo.description,
            instruction=odm_description_ar.concept_vo.instruction,
            sponsor_instruction=odm_description_ar.concept_vo.sponsor_instruction,
            library_name=odm_description_ar.library.name,
            start_date=odm_description_ar.item_metadata.start_date,
            end_date=odm_description_ar.item_metadata.end_date,
            status=odm_description_ar.item_metadata.status.value,
            version=odm_description_ar.item_metadata.version,
            change_description=odm_description_ar.item_metadata.change_description,
            author_username=odm_description_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in odm_description_ar.get_possible_actions()]
            ),
        )


class OdmDescriptionSimpleModel(BaseModel):
    @overload
    @classmethod
    def from_odm_description_uid(
        cls,
        uid: str,
        find_odm_description_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_description_uid(
        cls,
        uid: None,
        find_odm_description_by_uid: Callable[[str], ConceptARBase | None],
    ) -> None: ...
    @classmethod
    def from_odm_description_uid(
        cls,
        uid: str | None,
        find_odm_description_by_uid: Callable[[str], ConceptARBase | None],
    ) -> Self | None:
        simple_odm_description_model = None

        if uid is not None:
            odm_description = find_odm_description_by_uid(uid)

            if odm_description is not None:
                simple_odm_description_model = cls(
                    uid=uid,
                    name=odm_description.concept_vo.name,
                    language=odm_description.concept_vo.language,
                    description=odm_description.concept_vo.description,
                    instruction=odm_description.concept_vo.instruction,
                    sponsor_instruction=odm_description.concept_vo.sponsor_instruction,
                    version=odm_description.item_metadata.version,
                )
            else:
                simple_odm_description_model = cls(
                    uid=uid,
                    name=None,
                    language=None,
                    description=None,
                    instruction=None,
                    sponsor_instruction=None,
                    version=None,
                )
        return simple_odm_description_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    language: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    instruction: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    sponsor_instruction: Annotated[
        str | None, Field(json_schema_extra={"nullable": True, "format": "html"})
    ] = None
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class OdmDescriptionPostInput(ConceptPostInput):
    language: Annotated[str, Field(min_length=1)]
    description: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"format": "html"})
    ] = None
    instruction: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"format": "html"})
    ] = None
    sponsor_instruction: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"format": "html"})
    ] = None

    _date_validator = field_validator("language")(is_language_supported)


class OdmDescriptionPatchInput(ConceptPatchInput):
    name: Annotated[str, Field(min_length=1)]
    language: Annotated[str, Field(min_length=1)]
    description: Annotated[str | None, Field(min_length=1)]
    instruction: Annotated[str | None, Field(min_length=1)]
    sponsor_instruction: Annotated[str | None, Field(min_length=1)]

    _date_validator = field_validator("language")(is_language_supported)


class OdmDescriptionBatchPatchInput(ConceptPatchInput):
    uid: Annotated[str, Field(min_length=1)]
    language: Annotated[str | None, Field(min_length=1)]
    description: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"format": "html"})
    ]
    instruction: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"format": "html"})
    ]
    sponsor_instruction: Annotated[
        str | None, Field(min_length=1, json_schema_extra={"format": "html"})
    ]


class OdmDescriptionBatchInput(BatchInputModel):
    method: Annotated[
        str,
        Field(description="HTTP method corresponding to operation type", min_length=1),
    ]
    content: Annotated[OdmDescriptionBatchPatchInput | OdmDescriptionPostInput, Field()]


class OdmDescriptionBatchOutput(BaseModel):
    response_code: Annotated[
        int, Field(description="The HTTP response code related to input operation")
    ]
    content: Annotated[OdmDescription | None | BatchErrorResponse, Field()]


class OdmDescriptionVersion(OdmDescription):
    """
    Class for storing OdmDescription and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
