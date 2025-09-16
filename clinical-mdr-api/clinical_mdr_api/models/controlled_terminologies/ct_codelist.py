from typing import Annotated, Any, Self

from pydantic import Field

from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_name import (
    CTCodelistName,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, PostInputModel
from common.config import settings


class CTCodelist(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls,
        ct_codelist_name_ar: CTCodelistNameAR,
        ct_codelist_attributes_ar: CTCodelistAttributesAR,
    ) -> Self:
        return cls(
            catalogue_name=ct_codelist_attributes_ar.ct_codelist_vo.catalogue_name,
            codelist_uid=ct_codelist_attributes_ar.uid,
            parent_codelist_uid=ct_codelist_attributes_ar._ct_codelist_attributes_vo.parent_codelist_uid,
            child_codelist_uids=(
                ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids
                if ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids
                else []
            ),
            name=ct_codelist_attributes_ar.name,
            submission_value=ct_codelist_attributes_ar.ct_codelist_vo.submission_value,
            nci_preferred_name=ct_codelist_attributes_ar.ct_codelist_vo.preferred_term,
            definition=ct_codelist_attributes_ar.ct_codelist_vo.definition,
            extensible=ct_codelist_attributes_ar.ct_codelist_vo.extensible,
            library_name=Library.from_library_vo(
                ct_codelist_attributes_ar.library
            ).name,
            sponsor_preferred_name=ct_codelist_name_ar.name,
            template_parameter=ct_codelist_name_ar.ct_codelist_vo.is_template_parameter,
            possible_actions=sorted(
                [_.value for _ in ct_codelist_attributes_ar.get_possible_actions()]
            ),
        )

    catalogue_name: Annotated[str, Field()]

    codelist_uid: Annotated[str, Field()]

    parent_codelist_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    child_codelist_uids: list[str] = Field(default_factory=list)

    name: Annotated[str, Field()]

    submission_value: Annotated[str, Field()]

    nci_preferred_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    definition: Annotated[str, Field()]

    extensible: Annotated[bool, Field()]

    sponsor_preferred_name: Annotated[str, Field()]

    template_parameter: Annotated[bool, Field()]

    library_name: Annotated[str, Field()]
    possible_actions: list[str] = Field(
        description=(
            "Holds those actions that can be performed on the CTCodelistAttributes. "
            "Actions are: 'approve', 'edit', 'new_version'."
        ),
        default_factory=list,
    )


class CTCodelistTermInput(PostInputModel):
    term_uid: Annotated[str, Field(min_length=1)]
    order: Annotated[
        int,
        Field(gt=0, lt=settings.max_int_neo4j),
    ] = 999999


class CTCodelistCreateInput(PostInputModel):
    catalogue_name: Annotated[str, Field(min_length=1)]
    name: Annotated[str, Field(min_length=1)]
    submission_value: Annotated[str, Field(min_length=1)]
    nci_preferred_name: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str, Field(min_length=1)]
    extensible: Annotated[bool, Field()]
    sponsor_preferred_name: Annotated[str, Field(min_length=1)]
    template_parameter: Annotated[bool, Field()]
    parent_codelist_uid: Annotated[str | None, Field(min_length=1)] = None
    terms: Annotated[list[CTCodelistTermInput], Field()]
    library_name: Annotated[str, Field(min_length=1)]


class CTCodelistNameAndAttributes(BaseModel):
    @classmethod
    def from_ct_codelist_ar(
        cls,
        ct_codelist_name_ar: CTCodelistNameAR,
        ct_codelist_attributes_ar: CTCodelistAttributesAR,
    ) -> Self:
        codelist_name_and_attributes = cls(
            catalogue_name=ct_codelist_attributes_ar.ct_codelist_vo.catalogue_name,
            codelist_uid=ct_codelist_attributes_ar.uid,
            parent_codelist_uid=ct_codelist_attributes_ar._ct_codelist_attributes_vo.parent_codelist_uid,
            child_codelist_uids=ct_codelist_attributes_ar._ct_codelist_attributes_vo.child_codelist_uids,
            library_name=Library.from_library_vo(
                ct_codelist_attributes_ar.library
            ).name,
            name=CTCodelistName.from_ct_codelist_ar_without_common_codelist_fields(
                ct_codelist_name_ar
            ),
            attributes=CTCodelistAttributes.from_ct_codelist_ar_without_common_codelist_fields(
                ct_codelist_attributes_ar
            ),
        )

        return codelist_name_and_attributes

    catalogue_name: Annotated[str, Field()]

    codelist_uid: Annotated[str, Field()]

    parent_codelist_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    child_codelist_uids: list[Any] = Field(default_factory=list)

    library_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )

    name: Annotated[CTCodelistName, Field()]

    attributes: Annotated[CTCodelistAttributes, Field()]
