from neomodel import (
    BooleanProperty,
    DateProperty,
    IntegerProperty,
    JSONProperty,
    RelationshipFrom,
    RelationshipTo,
    StringProperty,
)

from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    UnitDefinitionRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)


class OdmDescriptionValue(ConceptValue):
    language = StringProperty()
    description = StringProperty()
    instruction = StringProperty()
    sponsor_instruction = StringProperty()


class OdmDescriptionRoot(ConceptRoot):
    has_form = RelationshipFrom("OdmFormRoot", "HAS_DESCRIPTION", model=ClinicalMdrRel)
    has_item_group = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_item = RelationshipFrom("OdmItemRoot", "HAS_DESCRIPTION", model=ClinicalMdrRel)
    has_condition = RelationshipFrom(
        "OdmConditionRoot", "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_method = RelationshipFrom(
        "OdmMethodRoot", "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_version = RelationshipTo(
        OdmDescriptionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmDescriptionValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmDescriptionValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmDescriptionValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmDescriptionValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmAliasValue(ConceptValue):
    context = StringProperty()


class OdmAliasRoot(ConceptRoot):
    has_condition = RelationshipFrom(
        "OdmConditionRoot", "HAS_ALIAS", model=ClinicalMdrRel
    )
    has_method = RelationshipFrom("OdmMethodRoot", "HAS_ALIAS", model=ClinicalMdrRel)
    has_form = RelationshipFrom("OdmFormRoot", "HAS_ALIAS", model=ClinicalMdrRel)
    has_item_group = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_ALIAS", model=ClinicalMdrRel
    )
    has_item = RelationshipFrom("OdmItemRoot", "HAS_ALIAS", model=ClinicalMdrRel)
    has_version = RelationshipTo(
        OdmAliasValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmAliasValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmAliasValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmAliasValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmAliasValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmConditionValue(ConceptValue):
    oid = StringProperty()


class OdmConditionRoot(ConceptRoot):
    has_formal_expression = RelationshipTo(
        "OdmFormalExpressionRoot", "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )
    has_description = RelationshipTo(
        OdmDescriptionRoot, "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS", model=ClinicalMdrRel)
    has_version = RelationshipTo(
        OdmConditionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmConditionValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        OdmConditionValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmConditionValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmConditionValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmMethodValue(ConceptValue):
    oid = StringProperty()
    method_type = StringProperty()


class OdmMethodRoot(ConceptRoot):
    has_formal_expression = RelationshipTo(
        "OdmFormalExpressionRoot", "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )
    has_description = RelationshipTo(
        OdmDescriptionRoot, "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS", model=ClinicalMdrRel)
    has_version = RelationshipTo(
        OdmMethodValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmMethodValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmMethodValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmMethodValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmMethodValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmFormalExpressionValue(ConceptValue):
    context = StringProperty()
    expression = StringProperty()


class OdmFormalExpressionRoot(ConceptRoot):
    has_condition = RelationshipFrom(
        OdmConditionRoot, "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )
    has_method = RelationshipFrom(
        OdmMethodRoot, "HAS_FORMAL_EXPRESSION", model=ClinicalMdrRel
    )
    has_version = RelationshipTo(
        OdmFormalExpressionValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmFormalExpressionValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmFormalExpressionValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmFormalExpressionValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmFormalExpressionValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


# pylint: disable=abstract-method
class OdmItemGroupRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    collection_exception_condition_oid = StringProperty()
    vendor = JSONProperty()


class OdmVendorNamespaceRelation(ClinicalMdrRel):
    value = StringProperty()


class OdmFormValue(ConceptValue):
    oid = StringProperty()
    repeating = BooleanProperty()
    sdtm_version = StringProperty()

    has_root = RelationshipFrom("OdmFormRoot", "HAS_VERSION", model=VersionRelationship)


class OdmFormRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    locked = BooleanProperty()
    collection_exception_condition_oid = StringProperty()


class OdmFormRoot(ConceptRoot):
    form_ref = RelationshipFrom(
        "OdmStudyEventRoot", "FORM_REF", model=OdmFormRefRelation
    )
    has_scope = RelationshipTo(CTTermRoot, "HAS_SCOPE")
    has_description = RelationshipTo(
        OdmDescriptionRoot, "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS", model=ClinicalMdrRel)
    has_activity_group = RelationshipTo(
        ActivityGroupRoot, "HAS_ACTIVITY_GROUP", model=ClinicalMdrRel
    )
    item_group_ref = RelationshipTo(
        "OdmItemGroupRoot", "ITEM_GROUP_REF", model=OdmItemGroupRefRelation
    )
    has_vendor_element = RelationshipTo(
        "OdmVendorElementRoot", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeRoot",
        "HAS_VENDOR_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    has_vendor_element_attribute = RelationshipTo(
        "OdmVendorAttributeRoot",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )

    has_version = RelationshipTo(OdmFormValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(OdmFormValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmFormValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmFormValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmFormValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmItemRefRelation(ClinicalMdrRel):
    order_number = IntegerProperty()
    mandatory = BooleanProperty()
    key_sequence = StringProperty()
    method_oid = StringProperty()
    imputation_method_oid = StringProperty()
    role = StringProperty()
    role_codelist_oid = StringProperty()
    collection_exception_condition_oid = StringProperty()
    vendor = JSONProperty()


class OdmItemGroupValue(ConceptValue):
    oid = StringProperty()
    repeating = BooleanProperty()
    is_reference_data = BooleanProperty()
    sas_dataset_name = StringProperty()
    origin = StringProperty()
    purpose = StringProperty()
    comment = StringProperty()

    has_root = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_VERSION", model=VersionRelationship
    )


class OdmItemGroupRoot(ConceptRoot):
    has_description = RelationshipTo(
        OdmDescriptionRoot, "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS", model=ClinicalMdrRel)
    has_sdtm_domain = RelationshipTo(
        CTTermRoot, "HAS_SDTM_DOMAIN", model=ClinicalMdrRel
    )
    has_activity_subgroup = RelationshipTo(
        ActivitySubGroupRoot, "HAS_ACTIVITY_SUB_GROUP", model=ClinicalMdrRel
    )
    item_group_ref = RelationshipFrom(
        OdmFormRoot, "ITEM_GROUP_REF", model=OdmItemGroupRefRelation
    )
    item_ref = RelationshipTo("OdmItemRoot", "ITEM_REF", model=OdmItemRefRelation)
    has_vendor_element = RelationshipTo(
        "OdmVendorElementRoot", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeRoot",
        "HAS_VENDOR_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    has_vendor_element_attribute = RelationshipTo(
        "OdmVendorAttributeRoot",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )

    has_version = RelationshipTo(
        OdmItemGroupValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(OdmItemGroupValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(
        OdmItemGroupValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmItemGroupValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmItemGroupValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmItemTermRelationship(ClinicalMdrRel):
    mandatory = BooleanProperty()
    order = IntegerProperty()
    display_text = StringProperty()


class OdmItemUnitDefinitionRelationship(ClinicalMdrRel):
    mandatory = BooleanProperty()
    order = IntegerProperty()


class OdmItemValue(ConceptValue):
    oid = StringProperty()
    prompt = StringProperty()
    datatype = StringProperty()
    length = IntegerProperty()
    significant_digits = IntegerProperty()
    sas_field_name = StringProperty()
    sds_var_name = StringProperty()
    origin = StringProperty()
    comment = StringProperty()

    has_root = RelationshipFrom("OdmItemRoot", "HAS_VERSION", model=VersionRelationship)


class OdmItemRoot(ConceptRoot):
    has_description = RelationshipTo(
        OdmDescriptionRoot, "HAS_DESCRIPTION", model=ClinicalMdrRel
    )
    has_alias = RelationshipTo(OdmAliasRoot, "HAS_ALIAS", model=ClinicalMdrRel)
    has_activity = RelationshipTo(ActivityRoot, "HAS_ACTIVITY", model=ClinicalMdrRel)
    has_unit_definition = RelationshipTo(
        UnitDefinitionRoot,
        "HAS_UNIT_DEFINITION",
        model=OdmItemUnitDefinitionRelationship,
    )
    has_codelist = RelationshipTo(CTCodelistRoot, "HAS_CODELIST", model=ClinicalMdrRel)
    has_codelist_term = RelationshipTo(
        CTTermRoot, "HAS_CODELIST_TERM", model=OdmItemTermRelationship
    )
    item_ref = RelationshipFrom(OdmItemGroupRoot, "ITEM_REF", model=OdmItemRefRelation)
    has_vendor_element = RelationshipTo(
        "OdmVendorElementRoot", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeRoot",
        "HAS_VENDOR_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    has_vendor_element_attribute = RelationshipTo(
        "OdmVendorAttributeRoot",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )

    has_version = RelationshipTo(OdmItemValue, "HAS_VERSION", model=VersionRelationship)
    has_latest_value = RelationshipTo(OdmItemValue, "LATEST", model=ClinicalMdrRel)
    latest_draft = RelationshipTo(OdmItemValue, "LATEST_DRAFT", model=ClinicalMdrRel)
    latest_final = RelationshipTo(OdmItemValue, "LATEST_FINAL", model=ClinicalMdrRel)
    latest_retired = RelationshipTo(
        OdmItemValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmStudyEventValue(ConceptValue):
    oid = StringProperty()
    effective_date = DateProperty()
    retired_date = DateProperty()
    description = StringProperty()
    display_in_tree = BooleanProperty()


class OdmStudyEventRoot(ConceptRoot):
    form_ref = RelationshipTo(OdmFormRoot, "FORM_REF", model=OdmFormRefRelation)
    has_version = RelationshipTo(
        OdmStudyEventValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmStudyEventValue, "LATEST", model=ClinicalMdrRel
    )

    latest_draft = RelationshipTo(
        OdmStudyEventValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmStudyEventValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmStudyEventValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmVendorNamespaceValue(ConceptValue):
    prefix = StringProperty()
    url = StringProperty()


class OdmVendorNamespaceRoot(ConceptRoot):
    has_vendor_element = RelationshipTo(
        "OdmVendorElementRoot", "HAS_VENDOR_ELEMENT", model=ClinicalMdrRel
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeRoot", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )

    has_version = RelationshipTo(
        OdmVendorNamespaceValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmVendorNamespaceValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmVendorAttributeValue(ConceptValue):
    compatible_types = JSONProperty()
    data_type = StringProperty()
    value_regex = StringProperty()


class OdmVendorAttributeRoot(ConceptRoot):
    belongs_to_vendor_namespace = RelationshipFrom(
        "OdmVendorNamespaceRoot", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )
    belongs_to_vendor_element = RelationshipFrom(
        "OdmVendorElementRoot", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )
    belongs_to_form = RelationshipFrom(
        "OdmFormRoot", "HAS_VENDOR_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_item_group = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_VENDOR_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_item = RelationshipFrom(
        "OdmItemRoot", "HAS_VENDOR_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_element_form = RelationshipFrom(
        "OdmFormRoot", "HAS_VENDOR_ELEMENT_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )
    belongs_to_element_item_group = RelationshipFrom(
        "OdmItemGroupRoot",
        "HAS_VENDOR_ELEMENT_ATTRIBUTE",
        model=OdmVendorNamespaceRelation,
    )
    belongs_to_element_item = RelationshipFrom(
        "OdmItemRoot", "HAS_VENDOR_ELEMENT_ATTRIBUTE", model=OdmVendorNamespaceRelation
    )

    has_version = RelationshipTo(
        OdmVendorAttributeValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmVendorAttributeValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmVendorAttributeValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmVendorAttributeValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmVendorAttributeValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )


class OdmVendorElementValue(ConceptValue):
    compatible_types = JSONProperty()


class OdmVendorElementRoot(ConceptRoot):
    belongs_to_vendor_namespace = RelationshipFrom(
        "OdmVendorNamespaceRoot", "HAS_VENDOR_ELEMENT", model=ClinicalMdrRel
    )
    belongs_to_form = RelationshipFrom(
        "OdmFormRoot", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    belongs_to_item_group = RelationshipFrom(
        "OdmItemGroupRoot", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    belongs_to_item = RelationshipFrom(
        "OdmItemRoot", "HAS_VENDOR_ELEMENT", model=OdmVendorNamespaceRelation
    )
    has_vendor_attribute = RelationshipTo(
        "OdmVendorAttributeRoot", "HAS_VENDOR_ATTRIBUTE", model=ClinicalMdrRel
    )

    has_version = RelationshipTo(
        OdmVendorElementValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        OdmVendorElementValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        OdmVendorElementValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        OdmVendorElementValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        OdmVendorElementValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
