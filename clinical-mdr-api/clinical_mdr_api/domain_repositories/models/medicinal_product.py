from neomodel import One, RelationshipFrom, RelationshipTo, ZeroOrMore, ZeroOrOne

from clinical_mdr_api.domain_repositories.models.compounds import CompoundRoot
from clinical_mdr_api.domain_repositories.models.concepts import (
    ConceptRoot,
    ConceptValue,
    NumericValueWithUnitRoot,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.pharmaceutical_product import (
    PharmaceuticalProductRoot,
)


class MedicinalProductValue(ConceptValue):
    medicinal_product_root = RelationshipFrom(
        "MedicinalProductRoot", "HAS_VERSION", model=VersionRelationship
    )

    has_pharmaceutical_product = RelationshipTo(
        PharmaceuticalProductRoot,
        "HAS_PHARMACEUTICAL_PRODUCT",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    is_compound = RelationshipTo(
        CompoundRoot,
        "IS_COMPOUND",
        cardinality=One,
        model=ClinicalMdrRel,
    )
    has_delivery_device = RelationshipTo(
        CTTermRoot, "HAS_DELIVERY_DEVICE", cardinality=ZeroOrOne, model=ClinicalMdrRel
    )
    has_dispenser = RelationshipTo(
        CTTermRoot,
        "HAS_DISPENSER",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )
    has_dose_value = RelationshipTo(
        NumericValueWithUnitRoot,
        "HAS_DOSE_VALUE",
        cardinality=ZeroOrMore,
        model=ClinicalMdrRel,
    )
    has_dose_frequency = RelationshipTo(
        CTTermRoot,
        "HAS_DOSE_FREQUENCY",
        cardinality=ZeroOrOne,
        model=ClinicalMdrRel,
    )


class MedicinalProductRoot(ConceptRoot):
    has_version = RelationshipTo(
        MedicinalProductValue, "HAS_VERSION", model=VersionRelationship
    )
    has_latest_value = RelationshipTo(
        MedicinalProductValue, "LATEST", model=ClinicalMdrRel
    )
    latest_draft = RelationshipTo(
        MedicinalProductValue, "LATEST_DRAFT", model=ClinicalMdrRel
    )
    latest_final = RelationshipTo(
        MedicinalProductValue, "LATEST_FINAL", model=ClinicalMdrRel
    )
    latest_retired = RelationshipTo(
        MedicinalProductValue, "LATEST_RETIRED", model=ClinicalMdrRel
    )
