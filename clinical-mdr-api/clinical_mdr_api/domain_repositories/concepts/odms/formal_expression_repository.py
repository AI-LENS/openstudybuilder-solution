from typing import Any

from clinical_mdr_api.domain_repositories.concepts.odms.odm_generic_repository import (
    OdmGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmFormalExpressionRoot,
    OdmFormalExpressionValue,
)
from clinical_mdr_api.domains.concepts.odms.formal_expression import (
    OdmFormalExpressionAR,
    OdmFormalExpressionVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_formal_expression import (
    OdmFormalExpression,
)
from common.utils import convert_to_datetime


class FormalExpressionRepository(OdmGenericRepository[OdmFormalExpressionAR]):
    root_class = OdmFormalExpressionRoot
    value_class = OdmFormalExpressionValue
    return_model = OdmFormalExpression

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmFormalExpressionAR:
        return OdmFormalExpressionAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmFormalExpressionVO.from_repository_values(
                context=value.context,
                expression=value.expression,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> OdmFormalExpressionAR:
        major, minor = input_dict["version"].split(".")
        odm_formal_expression_ar = OdmFormalExpressionAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=OdmFormalExpressionVO.from_repository_values(
                context=input_dict["context"],
                expression=input_dict["expression"],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=input_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: input_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=input_dict["change_description"],
                status=LibraryItemStatus(input_dict.get("status")),
                author_id=input_dict["author_id"],
                author_username=input_dict.get("author_username"),
                start_date=convert_to_datetime(value=input_dict["start_date"]),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

        return odm_formal_expression_ar

    def specific_alias_clause(self, _: list[Any] | None = None) -> str:
        return """
        WITH *,
        concept_value.context AS context,
        concept_value.expression AS expression
        """

    def _create_new_value_node(
        self, ar: OdmFormalExpressionAR
    ) -> OdmFormalExpressionValue:
        value_node = super()._create_new_value_node(ar=ar)

        value_node.save()

        value_node.context = ar.concept_vo.context
        value_node.expression = ar.concept_vo.expression

        return value_node

    def _has_data_changed(
        self, ar: OdmFormalExpressionAR, value: OdmFormalExpressionValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.context != value.context
            or ar.concept_vo.expression != value.expression
        )
