from collections import defaultdict
from typing import Any

from neomodel import db

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
    OdmDescriptionRoot,
    OdmDescriptionValue,
)
from clinical_mdr_api.domains.concepts.odms.description import (
    OdmDescriptionAR,
    OdmDescriptionVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.models.concepts.odms.odm_description import OdmDescription
from common.utils import convert_to_datetime


class DescriptionRepository(OdmGenericRepository[OdmDescriptionAR]):
    root_class = OdmDescriptionRoot
    value_class = OdmDescriptionValue
    return_model = OdmDescription

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: VersionRoot,
        library: Library,
        relationship: VersionRelationship,
        value: VersionValue,
        **_kwargs,
    ) -> OdmDescriptionAR:
        return OdmDescriptionAR.from_repository_values(
            uid=root.uid,
            concept_vo=OdmDescriptionVO.from_repository_values(
                name=value.name,
                language=value.language,
                description=value.description,
                instruction=value.instruction,
                sponsor_instruction=value.sponsor_instruction,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create_aggregate_root_instance_from_cypher_result(
        self, input_dict: dict[str, Any]
    ) -> OdmDescriptionAR:
        major, minor = input_dict["version"].split(".")
        odm_description_ar = OdmDescriptionAR.from_repository_values(
            uid=input_dict["uid"],
            concept_vo=OdmDescriptionVO.from_repository_values(
                name=input_dict["name"],
                language=input_dict["language"],
                description=input_dict.get("description"),
                instruction=input_dict.get("instruction"),
                sponsor_instruction=input_dict.get("sponsor_instruction"),
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

        return odm_description_ar

    def specific_alias_clause(self, _: list[Any] | None = None) -> str:
        return """
        WITH *,
        concept_value.language AS language,
        concept_value.description AS description,
        concept_value.instruction AS instruction,
        concept_value.sponsor_instruction AS sponsor_instruction
        """

    def _create_new_value_node(self, ar: OdmDescriptionAR) -> OdmDescriptionValue:
        value_node = super()._create_new_value_node(ar=ar)
        value_node.save()

        value_node.language = ar.concept_vo.language
        value_node.description = ar.concept_vo.description
        value_node.instruction = ar.concept_vo.instruction
        value_node.sponsor_instruction = ar.concept_vo.sponsor_instruction

        return value_node

    def _has_data_changed(
        self, ar: OdmDescriptionAR, value: OdmDescriptionValue
    ) -> bool:
        are_concept_properties_changed = super()._has_data_changed(ar=ar, value=value)

        return (
            are_concept_properties_changed
            or ar.concept_vo.language != value.language
            or ar.concept_vo.description != value.description
            or ar.concept_vo.instruction != value.instruction
            or ar.concept_vo.sponsor_instruction != value.sponsor_instruction
        )

    def get_parent_uids(self, description_uids: list[str]):
        """
        Fetches parent UIDs associated with the provided description UIDs.

        Args:
            description_uids (list[str]): List of ODM Description UIDs.

        Returns:
            dict[str, set[str]]: A dictionary mapping parent UIDs to sets of ODM Description UIDs.
        """
        rs = db.cypher_query(
            """
MATCH (dr:OdmDescriptionRoot)<-[:HAS_DESCRIPTION]-(pr:ConceptRoot)
WHERE dr.uid IN $uids
RETURN DISTINCT pr.uid, dr.uid ORDER BY pr.uid
""",
            params={"uids": description_uids},
        )

        parent_to_descriptions = defaultdict(set)
        if rs[0]:
            for item in rs[0]:
                parent_to_descriptions[item[0]].add(item[1])
            return parent_to_descriptions

        return {}
