from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_codelist_generic_repository import (
    CTCodelistGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTCodelistNameRoot,
    CTCodelistNameValue,
    CTCodelistRoot,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
    VersionRoot,
    VersionValue,
)
from clinical_mdr_api.domain_repositories.models.template_parameter import (
    TemplateParameterTermRoot,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameAR,
    CTCodelistNameVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.services.user_info import UserInfoService
from common.utils import convert_to_datetime


class CTCodelistNameRepository(CTCodelistGenericRepository[CTCodelistNameAR]):
    root_class = CTCodelistNameRoot
    value_class = CTCodelistNameValue
    relationship_from_root = "has_name_root"

    def codelist_specific_exists_by_name(self, codelist_name: str) -> bool:
        query = """
            MATCH (codelist_ver_root)-[:LATEST]->(codelist_ver_value:CTCodelistNameValue {name: $codelist_name})
            RETURN codelist_ver_value
            """

        result, _ = db.cypher_query(query, {"codelist_name": codelist_name})
        return len(result) > 0

    def _create_aggregate_root_instance_from_cypher_result(
        self, codelist_dict: dict[str, Any]
    ) -> CTCodelistNameAR:
        rel_data = codelist_dict["rel_data"]
        major, minor = rel_data.get("version").split(".")

        return CTCodelistNameAR.from_repository_values(
            uid=codelist_dict["codelist_uid"],
            ct_codelist_name_vo=CTCodelistNameVO.from_repository_values(
                name=codelist_dict.get("value_node").get("name"),
                catalogue_name=codelist_dict["catalogue_name"],
                is_template_parameter="TemplateParameter"
                in codelist_dict.get("value_node").labels,
            ),
            library=LibraryVO.from_input_values_2(
                library_name=codelist_dict["library_name"],
                is_library_editable_callback=(
                    lambda _: codelist_dict["is_library_editable"]
                ),
            ),
            item_metadata=LibraryItemMetadataVO.from_repository_values(
                change_description=rel_data.get("change_description"),
                status=LibraryItemStatus(rel_data.get("status")),
                author_id=rel_data.get("author_id"),
                author_username=UserInfoService.get_author_username_from_id(
                    rel_data.get("author_id")
                ),
                start_date=convert_to_datetime(value=rel_data.get("start_date")),
                end_date=None,
                major_version=int(major),
                minor_version=int(minor),
            ),
        )

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: CTCodelistNameRoot,
        library: Library,
        relationship: VersionRelationship,
        value: CTCodelistNameValue,
        **_kwargs,
    ) -> CTCodelistNameAR:
        ct_codelist_root_node = root.has_root.single()
        return CTCodelistNameAR.from_repository_values(
            uid=ct_codelist_root_node.uid,
            ct_codelist_name_vo=CTCodelistNameVO.from_repository_values(
                name=value.name,
                catalogue_name=ct_codelist_root_node.has_codelist.single().name,
                is_template_parameter=self.is_ct_node_a_tp(value),
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def _create(self, item: CTCodelistNameAR) -> CTCodelistNameAR:
        """
        Creates new CTCodelistNameAR, checks possibility based on library setting, then creates database representation,
        Creates CTCodelistNameRoot and CTCodelistNameValue database objects,
        recreates AR based on created database model and returns created AR.
        """
        relation_data: LibraryItemMetadataVO = item.item_metadata
        root = self.root_class()
        value = self.value_class(name=item.name)
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

        ct_codelist_root_node = CTCodelistRoot.nodes.get_or_none(uid=item.uid)
        ct_codelist_root_node.has_name_root.connect(root)
        self._maintain_parameters(item, root, value)

        return item

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: VersionRoot,
        value: VersionValue,
    ) -> None:
        """
        Method maintains TemplateParameter label when updating a codelist.
        :param versioned_object:
        :param root:
        :param value:
        :return None:
        """
        if versioned_object.ct_codelist_vo.is_template_parameter:
            query = """
                MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->(codelist_ver_value)
                SET codelist_ver_value:TemplateParameter
                WITH codelist_root, codelist_ver_value

                MATCH (codelist_root)-[:HAS_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
                MERGE (codelist_ver_value)-[hpt:HAS_PARAMETER_TERM]->(term_ver_root)

                SET term_ver_root:TemplateParameterTermRoot
                SET term_ver_value:TemplateParameterTermValue
            """
            db.cypher_query(query, {"codelist_uid": versioned_object.uid})
            TemplateParameterTermRoot.generate_node_uids_if_not_present()
        else:
            query = """
                MATCH (codelist_root:CTCodelistRoot {uid: $codelist_uid})-[:HAS_NAME_ROOT]->()-[:LATEST]->(codelist_ver_value)
                REMOVE codelist_ver_value:TemplateParameter
                WITH codelist_root, codelist_ver_value
                
                MATCH (codelist_root)-[:HAS_TERM]->(:CTTermRoot)-[:HAS_NAME_ROOT]->(term_ver_root)-[:LATEST]->(term_ver_value)
                MATCH (codelist_ver_value)-[hpt:HAS_PARAMETER_TERM]->(term_ver_root)
                DELETE hpt
                REMOVE term_ver_root.uid
                REMOVE term_ver_root:TemplateParameterTermRoot
                REMOVE term_ver_value:TemplateParameterTermValue
            """
            db.cypher_query(query, {"codelist_uid": versioned_object.uid})

    def is_repository_related_to_attributes(self) -> bool:
        return False
