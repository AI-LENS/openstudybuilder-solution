from typing import Annotated, Callable, Self, overload

from pydantic import Field, model_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.concept_base import ConceptARBase
from clinical_mdr_api.domains.concepts.odms.alias import OdmAliasAR
from clinical_mdr_api.domains.concepts.odms.description import OdmDescriptionAR
from clinical_mdr_api.domains.concepts.odms.item import (
    OdmItemAR,
    OdmItemRefVO,
    OdmItemTermVO,
    OdmItemUnitDefinitionVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_attribute import (
    OdmVendorAttributeAR,
    OdmVendorAttributeRelationVO,
    OdmVendorElementAttributeRelationVO,
)
from clinical_mdr_api.domains.concepts.odms.vendor_element import (
    OdmVendorElementRelationVO,
)
from clinical_mdr_api.domains.concepts.unit_definitions.unit_definition import (
    UnitDefinitionAR,
)
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesAR,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import CTTermNameAR
from clinical_mdr_api.domains.dictionaries.dictionary_term import DictionaryTermAR
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityHierarchySimpleModel,
)
from clinical_mdr_api.models.concepts.concept import (
    ConceptModel,
    ConceptPatchInput,
    ConceptPostInput,
)
from clinical_mdr_api.models.concepts.odms.odm_alias import OdmAliasSimpleModel
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmRefVendor,
    OdmRefVendorAttributeModel,
)
from clinical_mdr_api.models.concepts.odms.odm_description import (
    OdmDescriptionBatchPatchInput,
    OdmDescriptionPostInput,
    OdmDescriptionSimpleModel,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_attribute import (
    OdmVendorAttributeRelationModel,
    OdmVendorElementAttributeRelationModel,
)
from clinical_mdr_api.models.concepts.odms.odm_vendor_element import (
    OdmVendorElementRelationModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesSimpleModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleDictionaryTermModel,
    SimpleTermModel,
)
from clinical_mdr_api.models.utils import BaseModel, InputModel, PostInputModel
from common.config import settings


class OdmItemTermRelationshipModel(BaseModel):
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: str,
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: None,
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
    ) -> None: ...
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        term_uid: str | None,
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
    ) -> Self | None:
        simple_term_model = None

        if term_uid is not None:
            term = find_term_with_item_relation_by_item_uid(uid, term_uid)

            if term is not None:
                simple_term_model = cls(
                    term_uid=term_uid,
                    name=term.name,
                    mandatory=term.mandatory,
                    order=term.order,
                    display_text=term.display_text,
                    version=term.version,
                )
            else:
                simple_term_model = cls(
                    term_uid=term_uid,
                    name=None,
                    mandatory=False,
                    order=None,
                    display_text=None,
                    version=None,
                )
        return simple_term_model

    term_uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    mandatory: Annotated[bool, Field()] = False
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    display_text: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class OdmItemUnitDefinitionWithRelationship(BaseModel):
    @overload
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: str,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], ConceptARBase | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: None,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], ConceptARBase | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> None: ...
    @classmethod
    def from_unit_definition_uid(
        cls,
        uid: str | None,
        unit_definition_uid: str,
        find_unit_definition_by_uid: Callable[[str], ConceptARBase | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
    ) -> Self | None:
        simple_unit_definition_model = None

        if uid is not None:
            unit_definition_rel = find_unit_definition_with_item_relation_by_item_uid(
                uid, unit_definition_uid
            )
            unit_definition = find_unit_definition_by_uid(unit_definition_uid)

            if unit_definition is not None and unit_definition_rel is not None:
                if unit_definition.concept_vo.ucum_name is None:
                    ucum = SimpleTermModel.from_ct_code(
                        c_code=unit_definition.concept_vo.ucum_uid,
                        find_term_by_uid=find_dictionary_term_by_uid,
                    )
                else:
                    ucum = SimpleTermModel(
                        term_uid=unit_definition.concept_vo.ucum_uid,
                        name=unit_definition.concept_vo.ucum_name,
                    )

                ct_units = []
                for ct_unit in unit_definition.concept_vo.ct_units:
                    if ct_unit.name is None:
                        controlled_terminology_unit = SimpleTermModel.from_ct_code(
                            c_code=ct_unit.uid, find_term_by_uid=find_term_by_uid
                        )
                    else:
                        controlled_terminology_unit = SimpleTermModel(
                            term_uid=ct_unit.uid, name=ct_unit.name
                        )
                    ct_units.append(controlled_terminology_unit)

                simple_unit_definition_model = cls(
                    uid=unit_definition_uid,
                    name=unit_definition.concept_vo.name,
                    mandatory=unit_definition_rel.mandatory,
                    order=unit_definition_rel.order,
                    ucum=ucum,
                    ct_units=ct_units,
                )
            else:
                simple_unit_definition_model = cls(
                    uid=unit_definition_uid,
                    name=None,
                    mandatory=False,
                    order=None,
                    ucum=None,
                    ct_units=[],
                )
        return simple_unit_definition_model

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    mandatory: Annotated[bool, Field()] = False
    order: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    ucum: Annotated[
        SimpleTermModel | SimpleDictionaryTermModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    ct_units: list[SimpleTermModel] = Field(default_factory=list)


class OdmItem(ConceptModel):
    oid: Annotated[str | None, Field()]
    prompt: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    datatype: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    length: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = None
    significant_digits: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sas_field_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    sds_var_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    origin: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    comment: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    descriptions: Annotated[list[OdmDescriptionSimpleModel], Field()]
    aliases: Annotated[list[OdmAliasSimpleModel], Field()]
    unit_definitions: Annotated[list[OdmItemUnitDefinitionWithRelationship], Field()]
    codelist: Annotated[
        CTCodelistAttributesSimpleModel | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    terms: Annotated[list[OdmItemTermRelationshipModel], Field()]
    activity: Annotated[
        ActivityHierarchySimpleModel | None, Field(json_schema_extra={"nullable": True})
    ] = None
    vendor_elements: Annotated[list[OdmVendorElementRelationModel], Field()]
    vendor_attributes: Annotated[list[OdmVendorAttributeRelationModel], Field()]
    vendor_element_attributes: Annotated[
        list[OdmVendorElementAttributeRelationModel], Field()
    ]
    possible_actions: Annotated[list[str], Field()]

    @classmethod
    def from_odm_item_ar(
        cls,
        odm_item_ar: OdmItemAR,
        find_odm_description_by_uid: Callable[[str], OdmDescriptionAR | None],
        find_odm_alias_by_uid: Callable[[str], OdmAliasAR | None],
        find_unit_definition_by_uid: Callable[[str], UnitDefinitionAR | None],
        find_unit_definition_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemUnitDefinitionVO | None
        ],
        find_dictionary_term_by_uid: Callable[[str], DictionaryTermAR | None],
        find_term_by_uid: Callable[[str], CTTermNameAR | None],
        find_codelist_attribute_by_codelist_uid: Callable[
            [str], CTCodelistAttributesAR | None
        ],
        find_term_with_item_relation_by_item_uid: Callable[
            [str, str], OdmItemTermVO | None
        ],
        find_activity_by_uid: Callable[[str], ActivityAR | None],
        find_odm_vendor_element_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType], OdmVendorElementRelationVO | None
        ],
        find_odm_vendor_attribute_by_uid_with_odm_element_relation: Callable[
            [str, str, RelationType, bool],
            OdmVendorAttributeRelationVO | OdmVendorElementAttributeRelationVO | None,
        ],
    ) -> Self:
        return cls(
            uid=odm_item_ar._uid,
            oid=odm_item_ar.concept_vo.oid,
            name=odm_item_ar.name,
            prompt=odm_item_ar.concept_vo.prompt,
            datatype=odm_item_ar.concept_vo.datatype,
            length=odm_item_ar.concept_vo.length,
            significant_digits=odm_item_ar.concept_vo.significant_digits,
            sas_field_name=odm_item_ar.concept_vo.sas_field_name,
            sds_var_name=odm_item_ar.concept_vo.sds_var_name,
            origin=odm_item_ar.concept_vo.origin,
            comment=odm_item_ar.concept_vo.comment,
            library_name=odm_item_ar.library.name,
            start_date=odm_item_ar.item_metadata.start_date,
            end_date=odm_item_ar.item_metadata.end_date,
            status=odm_item_ar.item_metadata.status.value,
            version=odm_item_ar.item_metadata.version,
            change_description=odm_item_ar.item_metadata.change_description,
            author_username=odm_item_ar.item_metadata.author_username,
            descriptions=sorted(
                [
                    OdmDescriptionSimpleModel.from_odm_description_uid(
                        uid=description_uid,
                        find_odm_description_by_uid=find_odm_description_by_uid,
                    )
                    for description_uid in odm_item_ar.concept_vo.description_uids
                ],
                key=lambda item: item.name or "",
            ),
            aliases=sorted(
                [
                    OdmAliasSimpleModel.from_odm_alias_uid(
                        uid=alias_uid,
                        find_odm_alias_by_uid=find_odm_alias_by_uid,
                    )
                    for alias_uid in odm_item_ar.concept_vo.alias_uids
                ],
                key=lambda item: item.name or "",
            ),
            unit_definitions=sorted(
                [
                    OdmItemUnitDefinitionWithRelationship.from_unit_definition_uid(
                        uid=odm_item_ar._uid,
                        unit_definition_uid=unit_definition_uid,
                        find_unit_definition_by_uid=find_unit_definition_by_uid,
                        find_unit_definition_with_item_relation_by_item_uid=find_unit_definition_with_item_relation_by_item_uid,
                        find_dictionary_term_by_uid=find_dictionary_term_by_uid,
                        find_term_by_uid=find_term_by_uid,
                    )
                    for unit_definition_uid in odm_item_ar.concept_vo.unit_definition_uids
                ],
                key=lambda item: item.uid,
            ),
            codelist=CTCodelistAttributesSimpleModel.from_codelist_uid(
                uid=odm_item_ar.concept_vo.codelist_uid,
                find_codelist_attribute_by_codelist_uid=find_codelist_attribute_by_codelist_uid,
            ),
            terms=sorted(
                [
                    OdmItemTermRelationshipModel.from_odm_item_uid(
                        uid=odm_item_ar._uid,
                        term_uid=term_uid,
                        find_term_with_item_relation_by_item_uid=find_term_with_item_relation_by_item_uid,
                    )
                    for term_uid in odm_item_ar.concept_vo.term_uids
                ],
                key=lambda item: (item.order is not None, item.order),
            ),
            activity=ActivityHierarchySimpleModel.from_activity_uid(
                uid=odm_item_ar.concept_vo.activity_uid,
                find_activity_by_uid=find_activity_by_uid,
            ),
            vendor_elements=sorted(
                [
                    OdmVendorElementRelationModel.from_uid(
                        uid=vendor_element_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_element_by_uid_with_odm_element_relation,
                    )
                    for vendor_element_uid in odm_item_ar.concept_vo.vendor_element_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_attributes=sorted(
                [
                    OdmVendorAttributeRelationModel.from_uid(
                        uid=vendor_attribute_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,  # type: ignore[arg-type]
                        vendor_element_attribute=False,
                    )
                    for vendor_attribute_uid in odm_item_ar.concept_vo.vendor_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            vendor_element_attributes=sorted(
                [
                    OdmVendorElementAttributeRelationModel.from_uid(
                        uid=vendor_element_attribute_uid,
                        odm_element_uid=odm_item_ar._uid,
                        odm_element_type=RelationType.ITEM,
                        find_by_uid_with_odm_element_relation=find_odm_vendor_attribute_by_uid_with_odm_element_relation,  # type: ignore[arg-type]
                    )
                    for vendor_element_attribute_uid in odm_item_ar.concept_vo.vendor_element_attribute_uids
                ],
                key=lambda item: item.name or "",
            ),
            possible_actions=sorted(
                [_.value for _ in odm_item_ar.get_possible_actions()]
            ),
        )


class OdmItemRefModel(BaseModel):
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str,
        item_group_uid: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str], OdmItemRefVO | None
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self: ...
    @overload
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: None,
        item_group_uid: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str], OdmItemRefVO | None
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> None: ...
    @classmethod
    def from_odm_item_uid(
        cls,
        uid: str | None,
        item_group_uid: str,
        find_odm_item_by_uid_with_item_group_relation: Callable[
            [str, str], OdmItemRefVO | None
        ],
        find_odm_vendor_attribute_by_uid: Callable[[str], OdmVendorAttributeAR | None],
    ) -> Self | None:
        odm_item_ref_model = None

        if uid is not None:
            odm_item_ref_vo = find_odm_item_by_uid_with_item_group_relation(
                uid, item_group_uid
            )

            if odm_item_ref_vo is not None:
                odm_item_ref_model = cls(
                    uid=uid,
                    oid=odm_item_ref_vo.oid,
                    name=odm_item_ref_vo.name,
                    order_number=odm_item_ref_vo.order_number,
                    mandatory=odm_item_ref_vo.mandatory,
                    key_sequence=odm_item_ref_vo.key_sequence,
                    method_oid=odm_item_ref_vo.method_oid,
                    imputation_method_oid=odm_item_ref_vo.imputation_method_oid,
                    role=odm_item_ref_vo.role,
                    role_codelist_oid=odm_item_ref_vo.role_codelist_oid,
                    collection_exception_condition_oid=odm_item_ref_vo.collection_exception_condition_oid,
                    vendor=OdmRefVendor(
                        attributes=(
                            [
                                OdmRefVendorAttributeModel.from_uid(
                                    uid=attribute["uid"],
                                    value=attribute["value"],
                                    find_odm_vendor_attribute_by_uid=find_odm_vendor_attribute_by_uid,
                                )
                                for attribute in odm_item_ref_vo.vendor["attributes"]
                            ]
                            if odm_item_ref_vo.vendor
                            else []
                        )
                    ),
                )
            else:
                odm_item_ref_model = cls(
                    uid=uid,
                    oid=None,
                    name=None,
                    order_number=None,
                    mandatory=None,
                    key_sequence=None,
                    method_oid=None,
                    imputation_method_oid=None,
                    role=None,
                    role_codelist_oid=None,
                    collection_exception_condition_oid=None,
                    vendor=OdmRefVendor(attributes=[]),
                )
        return odm_item_ref_model

    uid: Annotated[str, Field()]
    oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    order_number: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    mandatory: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    key_sequence: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    method_oid: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    imputation_method_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    role: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    role_codelist_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    collection_exception_condition_oid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    vendor: Annotated[OdmRefVendor, Field()]


class OdmItemTermRelationshipInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    mandatory: Annotated[bool, Field()] = True
    order: Annotated[int | None, Field()] = 999999
    display_text: Annotated[str | None, Field()] = None


class OdmItemUnitDefinitionRelationshipInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    mandatory: Annotated[bool, Field()] = True
    order: Annotated[int | None, Field()] = 999999


def check_length_and_significant_digits(model):
    _datatype = (
        model.datatype.casefold() if isinstance(model.datatype, str) else model.datatype
    )

    if model.length is not None and _datatype not in [
        "text",
        "string",
        "integer",
        "float",
    ]:
        raise ValueError(
            "When datatype is not 'text', 'string', 'integer' or 'float', length must be null."
        )
    if model.length is None and _datatype in ["text", "string"]:
        raise ValueError(
            "When datatype is 'text' or 'string', length must be provided."
        )

    if _datatype == "float" and (
        bool(model.length is not None) ^ bool(model.significant_digits is not None)
    ):
        raise ValueError(
            "When datatype is 'float', both length and significant_digits must be provided together, or both must be null."
        )
    return model


class OdmItemPostInput(ConceptPostInput):
    oid: Annotated[str | None, Field(min_length=1)] = None
    datatype: Annotated[str, Field(min_length=1)]
    prompt: Annotated[str | None, Field()] = None
    length: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)] = None
    significant_digits: Annotated[
        int | None, Field(ge=0, lt=settings.max_int_neo4j)
    ] = None
    sas_field_name: Annotated[str | None, Field()] = None
    sds_var_name: Annotated[str | None, Field()] = None
    origin: Annotated[str | None, Field()] = None
    comment: Annotated[str | None, Field()] = None
    descriptions: list[OdmDescriptionPostInput | str] = Field(default_factory=list)
    alias_uids: list[str] = Field(default_factory=list)
    codelist_uid: Annotated[str | None, Field(min_length=1)] = None
    unit_definitions: list[OdmItemUnitDefinitionRelationshipInput] = Field(
        default_factory=list
    )
    terms: list[OdmItemTermRelationshipInput] = Field(default_factory=list)

    _ = model_validator(mode="after")(check_length_and_significant_digits)


class OdmItemPatchInput(ConceptPatchInput):
    name: Annotated[str, Field(min_length=1)]
    oid: Annotated[str | None, Field(min_length=1)]
    datatype: Annotated[str | None, Field(min_length=1)]
    prompt: Annotated[str | None, Field()]
    length: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)]
    significant_digits: Annotated[int | None, Field(ge=0, lt=settings.max_int_neo4j)]
    sas_field_name: Annotated[str | None, Field()]
    sds_var_name: Annotated[str | None, Field()]
    origin: Annotated[str | None, Field()]
    comment: Annotated[str | None, Field()]
    descriptions: Annotated[
        list[OdmDescriptionBatchPatchInput | OdmDescriptionPostInput | str], Field()
    ]
    alias_uids: Annotated[list[str], Field()]
    unit_definitions: Annotated[list[OdmItemUnitDefinitionRelationshipInput], Field()]
    codelist_uid: Annotated[str | None, Field(min_length=1)]
    terms: Annotated[list[OdmItemTermRelationshipInput], Field()]

    _ = model_validator(mode="after")(check_length_and_significant_digits)


class OdmItemActivityPostInput(PostInputModel):
    uid: Annotated[str, Field(min_length=1)]


class OdmItemVersion(OdmItem):
    """
    Class for storing OdmItem and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
