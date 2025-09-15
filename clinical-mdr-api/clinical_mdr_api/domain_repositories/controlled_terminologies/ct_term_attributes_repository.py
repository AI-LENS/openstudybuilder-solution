from datetime import datetime, timezone
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories._utils.helpers import is_codelist_in_final
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_get_all_query_utils import (
    create_term_attributes_aggregate_instances_from_cypher_result,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_generic_repository import (
    CTTermGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistRoot,
    CTTermAttributesRoot,
    CTTermAttributesValue,
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
    CTTermCodelistVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryVO,
)
from common.exceptions import BusinessLogicException


class CTTermAttributesRepository(CTTermGenericRepository[CTTermAttributesAR]):
    root_class = CTTermAttributesRoot
    value_class = CTTermAttributesValue
    relationship_from_root = "has_attributes_root"

    def term_specific_exists_by_name(self, term_name: str) -> bool:
        # We allow duplicates under the condition that the conflicting term is retired
        query = """
            MATCH (term_ver_root:CTTermAttributesRoot)-[:LATEST]->(term_ver_value:CTTermAttributesValue {name_submission_value: $term_name})
            OPTIONAL MATCH (term_ver_root)-[retired:HAS_VERSION {status: 'Retired'}]-(term_ver_value)
            WITH * WHERE NOT (retired IS NOT NULL AND retired.end_date IS NULL)
            RETURN term_ver_value
            """
        result, _ = db.cypher_query(query, {"term_name": term_name})
        return len(result) > 0

    def term_attributes_exists_by_code_submission_value(
        self, term_code_submission_value: str
    ) -> bool:
        # We allow duplicates under the condition that the conflicting term is retired
        query = """
            MATCH (term_ver_root:CTTermAttributesRoot)-[:LATEST]->
                (term_ver_value:CTTermAttributesValue {code_submission_value: $term_code_submission_value})
            OPTIONAL MATCH (term_ver_root)-[retired:HAS_VERSION {status: 'Retired'}]-(term_ver_value)
            WITH * WHERE NOT (retired IS NOT NULL AND retired.end_date IS NULL)
            RETURN term_ver_value
            """
        result, _ = db.cypher_query(
            query, {"term_code_submission_value": term_code_submission_value}
        )
        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, term_dict: dict[str, Any]
    ) -> CTTermAttributesAR:
        return create_term_attributes_aggregate_instances_from_cypher_result(
            term_dict=term_dict, is_aggregated_query=False
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTTermAttributesRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CTTermAttributesValue,
        **_kwargs,
    ) -> CTTermAttributesAR:
        ct_term_root_node = root.has_root.single()
        ct_codelist_root_node = ct_term_root_node.has_term.single()
        if not ct_codelist_root_node:
            ct_codelist_root_node = ct_term_root_node.had_term.single()

        codelists: list[CTTermCodelistVO] = []
        for codelist_root in ct_term_root_node.has_term.all():
            codelists.append(
                CTTermCodelistVO(
                    codelist_uid=codelist_root.uid,
                    order=codelist_root.has_term.relationship(ct_term_root_node).order,
                    library_name=codelist_root.has_library.single().name,
                )
            )

        return CTTermAttributesAR.from_repository_values(
            uid=ct_term_root_node.uid,
            ct_term_attributes_vo=CTTermAttributesVO.from_repository_values(
                codelists=codelists,
                concept_id=value.concept_id,
                code_submission_value=value.code_submission_value,
                name_submission_value=value.name_submission_value,
                preferred_term=value.preferred_term,
                definition=value.definition,
                catalogue_name=ct_codelist_root_node.has_codelist.single().name,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _is_new_version_necessary(
        self, ar: CTTermAttributesAR, value: VersionValue
    ) -> bool:
        return self._has_data_changed(ar, value)

    def _get_or_create_value(
        self, root: CTTermAttributesRoot, ar: CTTermAttributesAR
    ) -> CTTermAttributesValue:
        for itm in root.has_version.filter(
            code_submission_value=ar.ct_term_vo.code_submission_value,
            name_submission_value=ar.ct_term_vo.name_submission_value,
            preferred_term=ar.ct_term_vo.preferred_term,
            definition=ar.ct_term_vo.definition,
        ):
            return itm
        latest_draft = root.latest_draft.get_or_none()
        if latest_draft and not self._has_data_changed(ar, latest_draft):
            return latest_draft
        latest_final = root.latest_final.get_or_none()
        if latest_final and not self._has_data_changed(ar, latest_final):
            return latest_final
        latest_retired = root.latest_retired.get_or_none()
        if latest_retired and not self._has_data_changed(ar, latest_retired):
            return latest_retired
        new_value = self.value_class(
            code_submission_value=ar.ct_term_vo.code_submission_value,
            name_submission_value=ar.ct_term_vo.name_submission_value,
            preferred_term=ar.ct_term_vo.preferred_term,
            definition=ar.ct_term_vo.definition,
        )
        self._db_save_node(new_value)
        return new_value

    def _has_data_changed(self, ar: CTTermAttributesAR, value: VersionValue):
        return (
            ar.ct_term_vo.name_submission_value != value.name_submission_value
            or ar.ct_term_vo.code_submission_value != value.code_submission_value
            or ar.ct_term_vo.preferred_term != value.preferred_term
            or ar.ct_term_vo.definition != value.definition
        )

    def _create(self, item: CTTermAttributesAR) -> CTTermAttributesAR:
        """
        Creates new CTTermAttributesAR, checks possibility based on
        library setting, then creates database representation.
        Creates CTTermRoot, CTTermAttributesRoot and CTTermAttributesValue database object,
        recreates AR based on created database model and returns created AR.
        It also creates relationships to associated CTCodelistRoot and Library.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class()
        value = self.value_class(
            code_submission_value=item.ct_term_vo.code_submission_value,
            name_submission_value=item.ct_term_vo.name_submission_value,
            preferred_term=item.ct_term_vo.preferred_term,
            definition=item.ct_term_vo.definition,
        )
        self._db_save_node(root)

        (
            root,
            value,
            _,
            _,
            _,
        ) = self._db_create_and_link_nodes(
            root, value, self._library_item_metadata_vo_to_datadict(relation_data)
        )

        ct_term_root_node = CTTermRoot(uid=item.uid)
        ct_term_root_node.save()
        ct_term_root_node.has_attributes_root.connect(root)

        library = self._get_library(item.library.name)
        ct_term_root_node.has_library.connect(library)

        ct_codelist_root_node = CTCodelistRoot.nodes.get_or_none(
            uid=item.ct_term_vo.codelists[0].codelist_uid
        )
        ct_term_root_node.has_term.connect(
            ct_codelist_root_node,
            {
                "start_date": datetime.now(timezone.utc),
                "end_date": None,
                "author_id": item.item_metadata.author_id,
            },
        )

        # Validate that the term is added to a codelist that isn't in a draft state.
        BusinessLogicException.raise_if_not(
            is_codelist_in_final(ct_codelist_root_node),
            msg=f"Term with UID '{item.uid}' cannot be added to Codelist with UID '{item.ct_term_vo.codelists[0].codelist_uid}' as the codelist is in a draft state.",
        )

        self._maintain_parameters(item, root, value)

        return item

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def is_repository_related_to_attributes(self) -> bool:
        """
        The method created to allow CTTermGenericRepository interface to handle filtering by package
        in different way for CTTermAttributesRepository and for CTTermNameRepository.
        :return:
        """
        return True
