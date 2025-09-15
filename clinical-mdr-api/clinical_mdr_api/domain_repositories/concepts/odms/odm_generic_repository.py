from abc import ABC
from typing import Any

from neomodel import db

from clinical_mdr_api.domain_repositories._generic_repository_interface import (
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.concepts.concept_generic_repository import (
    ConceptGenericRepository,
)
from clinical_mdr_api.domain_repositories.models.activities import (
    ActivityGroupRoot,
    ActivityRoot,
    ActivitySubGroupRoot,
)
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.odm import (
    OdmFormRoot,
    OdmItemGroupRoot,
    OdmItemRoot,
    OdmVendorAttributeRoot,
    OdmVendorElementRoot,
)
from clinical_mdr_api.domains._utils import ObjectStatus
from clinical_mdr_api.domains.concepts.utils import RelationType
from clinical_mdr_api.models.concepts.odms.odm_common_models import (
    OdmElementWithParentUid,
)
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
    sb_clear_cache,
)
from common.exceptions import BusinessLogicException


class OdmGenericRepository(ConceptGenericRepository[_AggregateRootType], ABC):
    def find_all(
        self,
        library: str | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        return_all_versions: bool = False,
        only_specific_status: str = ObjectStatus.LATEST.name,
        **kwargs,
    ) -> tuple[list[_AggregateRootType], int]:
        """
        Method runs a cypher query to fetch all needed data to create objects of type AggregateRootType.
        In the case of the following repository it will be some Concept aggregates.

        It uses cypher instead of neomodel as neomodel approach triggered some performance issues, because it is needed
        to traverse many relationships to fetch all needed data and each traversal is separate database call when using
        neomodel.
        :param library:
        :param sort_by:
        :param page_number:
        :param page_size:
        :param filter_by:
        :param filter_operator:
        :param total_count:
        :param return_all_versions:
        :param only_specific_status:
        :return GenericFilteringReturn[_AggregateRootType]:
        """
        match_clause = self.generic_match_clause(only_specific_status)

        filter_statements, filter_query_parameters = self.create_query_filter_statement(
            library=library, **kwargs
        )
        match_clause += filter_statements

        alias_clause = self.generic_alias_clause() + self.specific_alias_clause(
            only_specific_status
        )
        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=self.return_model,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()
        extracted_items = self._retrieve_concepts_from_cypher_res(
            result_array, attributes_names
        )

        count_result, _ = db.cypher_query(
            query=query.count_query, params=query.parameters
        )
        total_amount = (
            count_result[0][0] if len(count_result) > 0 and total_count else 0
        )

        return extracted_items, total_amount

    @classmethod
    def _get_origin_and_relation_node(
        cls, uid: str, relation_uid: str | None, relationship_type: RelationType
    ):
        root_class_node = cls.root_class.nodes.get_or_none(uid=uid)

        relation_mapping = {
            RelationType.ACTIVITY_GROUP: (ActivityGroupRoot, "has_activity_group"),
            RelationType.ACTIVITY_SUB_GROUP: (
                ActivitySubGroupRoot,
                "has_activity_subgroup",
            ),
            RelationType.ACTIVITY: (ActivityRoot, "has_activity"),
            RelationType.ITEM_GROUP: (OdmItemGroupRoot, "item_group_ref"),
            RelationType.ITEM: (OdmItemRoot, "item_ref"),
            RelationType.FORM: (OdmFormRoot, "form_ref"),
            RelationType.TERM: (CTTermRoot, "has_codelist_term"),
            RelationType.UNIT_DEFINITION: (UnitDefinitionRoot, "has_unit_definition"),
            RelationType.VENDOR_ELEMENT: (OdmVendorElementRoot, "has_vendor_element"),
            RelationType.VENDOR_ATTRIBUTE: (
                OdmVendorAttributeRoot,
                "has_vendor_attribute",
            ),
            RelationType.VENDOR_ELEMENT_ATTRIBUTE: (
                OdmVendorAttributeRoot,
                "has_vendor_element_attribute",
            ),
        }

        BusinessLogicException.raise_if(
            relationship_type not in relation_mapping, msg="Invalid relation type."
        )

        relation_node_cls, origin_label = relation_mapping[relationship_type]
        relation_node = relation_node_cls.nodes.get_or_none(uid=relation_uid)

        BusinessLogicException.raise_if(
            not relation_node and relation_uid,
            msg=f"Object with UID '({relation_uid}' doesn't exist.",
        )

        return getattr(root_class_node, origin_label), relation_node

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def add_relation(
        self,
        uid: str,
        relation_uid: str,
        relationship_type: RelationType,
        parameters: dict[str, Any] | None = None,
    ) -> None:
        origin, relation_node = self.__class__._get_origin_and_relation_node(
            uid, relation_uid, relationship_type
        )

        origin.disconnect(relation_node)

        if isinstance(parameters, dict):
            origin.connect(relation_node, parameters)
        else:
            origin.connect(relation_node)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def remove_relation(
        self,
        uid: str,
        relation_uid: str | None,
        relationship_type: RelationType,
        disconnect_all: bool = False,
    ) -> None:
        origin, relation_node = self.__class__._get_origin_and_relation_node(
            uid, relation_uid, relationship_type
        )

        if disconnect_all:
            origin.disconnect_all()
        else:
            origin.disconnect(relation_node)

    def has_active_relationships(
        self, uid: str, relationships: list[Any], all_exist: bool = False
    ) -> bool:
        """
        Checks if the node has active relationships.

        :param uid: The uid of the node to check relationships on.
        :param relationships: A list of relationship names to check the existence of.
        :param all_exist: If True, all provided relationships must exist on the node. If False, at least one of the provided relationships must exist.
        :return: Returns True, if the relationships exist, otherwise False.
        """
        root = self.root_class.nodes.get_or_none(uid=uid)

        try:
            if not all_exist:
                for relationship in relationships:
                    if getattr(root, relationship):
                        return True

                return False
            for relationship in relationships:
                if not getattr(root, relationship):
                    return False

            return True
        except AttributeError as exc:
            raise AttributeError(f"{relationship} relationship was not found.") from exc

    def get_active_relationships(
        self, uid: str, relationships: list[Any]
    ) -> dict[str, list[str]]:
        """
        Returns a key-pair value of target node's name and a list of uids of nodes connected to source node.

        :param uid: The uid of the source node to check relationships on.
        :param relationships: A list of relationship names to check the existence of.
        :return: Returns a dict.
        """
        source_node = self.root_class.nodes.get_or_none(uid=uid)

        try:
            rs: dict[str, list[str]] = {}
            for relationship in relationships:
                rel = getattr(source_node, relationship)
                if rel:
                    for target_node in rel.all():
                        target_node_without_suffix = target_node.__label__.removesuffix(
                            "Root"
                        )
                        if target_node_without_suffix not in rs:
                            rs[target_node_without_suffix] = [target_node.uid]
                        else:
                            rs[target_node_without_suffix].append(target_node.uid)
            return rs
        except AttributeError as exc:
            raise AttributeError(f"{relationship} relationship was not found.") from exc

    def get_if_has_relationship(self, relationship: str):
        """
        Returns a list of ODM Element uid and name with their parent uids.
        """
        roots = self.root_class.nodes.has(**{relationship: True})

        rs = []
        for root in roots:
            parents = getattr(root, relationship).all()

            rs.append(
                OdmElementWithParentUid(
                    uid=root.uid,
                    name=root.has_latest_value.get_or_none().name,
                    parent_uids=[parent.uid for parent in parents],
                )
            )

        return rs

    def odm_object_exists(
        self,
        library_name: str | None = None,
        description_uids: list[str] | None = None,
        alias_uids: list[str] | None = None,
        sdtm_domain_uids: list[str] | None = None,
        term_uids: list[str] | None = None,
        unit_definition_uids: list[str] | None = None,
        formal_expression_uids: list[str] | None = None,
        scope_uid: str | None = None,
        codelist_uid: str | None = None,
        **value_attributes,
    ):
        """
        Checks whether an ODM object exists in the database based on various filtering criteria.
        This method constructs a Cypher query dynamically using the provided UID lists
        and additional value node attributes to search for matching objects in the database.

        Args:
            description_uids (list[str] | None): List of UIDs for ODM Descriptions to match.
            alias_uids (list[str] | None): List of UIDs for ODM Aliases to match.
            sdtm_domain_uids (list[str] | None): List of UIDs for SDTM Domains to match.
            term_uids (list[str] | None): List of UIDs for terms to match in CT Codelist Terms.
            unit_definition_uids (list[str] | None): List of UIDs for Unit Definitions to match.
            formal_expression_uids (list[str] | None): List of UIDs for ODM Formal Expressions to match.
            scope_uid (str | None): UID for a specific scope to match.
            codelist_uid (str | None): UID for a CT Codelist to match.
            library_name (str | None): Name of the library to match.
            **value_attributes: Arbitrary key-value pairs to match against properties of the ODM object.

        Returns:
            list[str] | None: Returns a list of the UIDs of the matching ODM objects if it exist, otherwise returns `None`.
        """
        if not description_uids:
            description_uids = []
        if not alias_uids:
            alias_uids = []
        if not sdtm_domain_uids:
            sdtm_domain_uids = []
        if not term_uids:
            term_uids = []
        if not unit_definition_uids:
            unit_definition_uids = []
        if not formal_expression_uids:
            formal_expression_uids = []

        query = f"""
            MATCH (root:{self.root_class.__label__})-[:LATEST]->(value:{self.value_class.__label__})
        """

        params: dict[str, Any] = {}

        if library_name:
            query += (
                " MATCH (:Library {name: $library_name})-[:CONTAINS_CONCEPT]->(root) "
            )
            params["library_name"] = library_name

        if description_uids:
            query += " MATCH (desc_root:OdmDescriptionRoot)<-[:HAS_DESCRIPTION]-(root) "
            params["description_uids"] = description_uids

        if alias_uids:
            query += " MATCH (alias_root:OdmAliasRoot)<-[:HAS_ALIAS]-(root) "
            params["alias_uids"] = alias_uids

        if scope_uid:
            query += " MATCH (:CTTermRoot {uid: $scope_uid})<-[:HAS_SCOPE]-(root) "
            params["scope_uid"] = scope_uid

        if sdtm_domain_uids:
            query += " MATCH (ct_term_root:CTTermRoot)<-[:HAS_SDTM_DOMAIN]-(root) "
            params["sdtm_domain_uids"] = sdtm_domain_uids

        if codelist_uid:
            query += (
                " MATCH (:CTCodelistRoot {uid: $codelist_uid})<-[:HAS_CODELIST]-(root) "
            )
            params["codelist_uid"] = codelist_uid

        if term_uids:
            params["term_uids"] = term_uids
            query += " MATCH (ct_term_root:CTTermRoot)<-[:HAS_CODELIST_TERM]-(root) "

        if unit_definition_uids:
            params["unit_definition_uids"] = unit_definition_uids
            query += " MATCH (unit_definition_root:UnitDefinitionRoot)<-[:HAS_UNIT_DEFINITION]-(root) "

        if formal_expression_uids:
            params["formal_expression_uids"] = formal_expression_uids
            query += " MATCH (odm_formal_expression:OdmFormalExpressionRoot)<-[:HAS_FORMAL_EXPRESSION]-(root) "

        wheres = []
        for key, value in value_attributes.items():
            if value is not None:
                wheres.append(f"value.{key} = ${key}")

                params[key] = value
            else:
                wheres.append(f"value.{key} IS NULL")

        query += " WHERE " + " AND ".join(wheres)

        _where = []
        # pylint: disable=too-many-boolean-expressions
        if (
            description_uids
            or alias_uids
            or description_uids
            or alias_uids
            or sdtm_domain_uids
            or term_uids
            or unit_definition_uids
            or formal_expression_uids
        ):
            query += " WITH root"

            if description_uids:
                query += ", apoc.coll.sort(COLLECT(DISTINCT desc_root.uid)) AS description_uids"
                _where.append("description_uids = apoc.coll.sort($description_uids)")

            if alias_uids:
                query += (
                    ", apoc.coll.sort(COLLECT(DISTINCT alias_root.uid)) AS alias_uids"
                )
                _where.append("alias_uids = apoc.coll.sort($alias_uids)")

            if sdtm_domain_uids:
                query += ", apoc.coll.sort(COLLECT(DISTINCT ct_term_root.uid)) AS sdtm_domain_uids"
                _where.append("sdtm_domain_uids = apoc.coll.sort($sdtm_domain_uids)")

            if term_uids:
                query += (
                    ", apoc.coll.sort(COLLECT(DISTINCT ct_term_root.uid)) AS term_uids"
                )
                _where.append("term_uids = apoc.coll.sort($term_uids)")

            if unit_definition_uids:
                query += ", apoc.coll.sort(COLLECT(DISTINCT unit_definition_root.uid)) AS unit_definition_uids"
                _where.append(
                    "unit_definition_uids = apoc.coll.sort($unit_definition_uids)"
                )

            if formal_expression_uids:
                query += ", apoc.coll.sort(COLLECT(DISTINCT odm_formal_expression.uid)) AS formal_expression_uids"
                _where.append(
                    "formal_expression_uids = apoc.coll.sort($formal_expression_uids)"
                )

        if _where:
            query += " WHERE " + " AND ".join(_where)

        query += " RETURN root.uid"

        rs = db.cypher_query(query=query, params=params)

        if rs[0]:
            return rs[0][0]

        return None
