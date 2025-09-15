from dataclasses import dataclass
from typing import Any, Mapping

from cachetools import TTLCache
from neomodel import RelationshipDefinition, RelationshipManager

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    VersionRelationship,
    VersionRoot,
)
from clinical_mdr_api.domain_repositories.models.study_audit_trail import StudyAction
from clinical_mdr_api.domain_repositories.models.study_field import StudyField
from clinical_mdr_api.domain_repositories.models.study_selections import StudySelection
from clinical_mdr_api.repositories._utils import sb_clear_cache
from common.config import settings
from common.exceptions import ValidationException


class EntityNotFoundError(LookupError):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return self.msg


@dataclass(frozen=True)
class RepositoryClosureData:
    not_for_update: bool
    repository: Any
    additional_closure: Any


class RepositoryImpl:
    """
    A repository is responsible for reading/writing data to/from the database.
    Results from a repository should be used to build aggregate root (AR) objects.
    """

    cache_store_item_by_uid = TTLCache(
        maxsize=settings.cache_max_size, ttl=settings.cache_ttl
    )

    value_class: type
    root_class: type

    @property
    def author_id(self) -> str | None:
        return self._author_id

    def __init__(self, user: str | None = None):
        self._author_id = user

    def _get_version_relation_keys(self, root_node: VersionRoot) -> tuple[
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
        RelationshipDefinition,
    ]:
        """
        Returns the keys used in the neomodel definition for the relationship definition.
        By default, all library objects use "has_version", "has_draft", etc...
        But some objects use an override, like SponsorModel with "has_sponsor_model_version"

        Args:
            root_node (VersionRoot): Root node for which to return the relationship manager

        Returns:
            The relationships managers for the various versioning relationships.
        """
        return (
            root_node.has_version,
            root_node.has_latest_value,
            root_node.latest_draft,
            root_node.latest_final,
            root_node.latest_retired,
        )

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_create_and_link_nodes(
        self,
        root: ClinicalMdrNode,
        value: ClinicalMdrNode,
        rel_properties: Mapping[str, Any],
        save_root: bool = True,
    ):
        """
        Creates versioned root and versioned object nodes.
        # TODO - GEneration of uids should be removed (additional service?)
        """
        if save_root:
            self._db_save_node(root)
        self._db_save_node(value)

        (
            has_version,
            has_latest_value,
            latest_draft,
            latest_final,
            _,
        ) = self._get_version_relation_keys(root)
        latest_value = self._db_create_relationship(has_latest_value, value)
        self._db_create_relationship(has_version, value, rel_properties)

        if rel_properties["status"] != "Final":
            latest_draft = self._db_create_relationship(latest_draft, value)
            latest_final = None
        else:
            # if we create an object that is immediately in a final state, we create a LATEST_FINAL relationship.
            latest_draft = None
            latest_final = self._db_create_relationship(latest_final, value)
        return root, value, latest_value, latest_draft, latest_final

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_save_node(self, node: ClinicalMdrNode) -> ClinicalMdrNode:
        """
        Saves a Neomodel node object in the graph.
        TODO: optionally accept multiple nodes and handle in same DB transaction.
        """
        if node is not None:
            node.save()
        return node

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_create_relationship(
        self,
        origin: RelationshipManager,
        destination: ClinicalMdrNode,
        parameters: Mapping[str, Any] | None = None,
    ) -> VersionRelationship:
        """
        Creates a relationship of an origin type (e.g.VersionRoot.has_latest) to a destination (VersionValue).
        Parameters of a VersionRelationship must be included.
        """
        if parameters is None:
            parameters = {}

        if parameters:
            return origin.connect(destination, parameters)
        return origin.connect(destination)

    @sb_clear_cache(caches=["cache_store_item_by_uid"])
    def _db_remove_relationship(
        self, relationship: RelationshipManager, value: ClinicalMdrNode | None = None
    ):
        """
        Removes a relationship.
        Example input: {relationship: compound_root.latest_draft,
                        value: compound_value}
        """
        if value is None:
            relationship.disconnect_all()
        else:
            relationship.disconnect(value)

    def generate_uid_callback(self):
        return self.root_class.get_next_free_uid_and_increment_counter()


def get_connected_node_by_rel_name_and_study_value(
    node: Any,
    connected_rel_name: str,
    study_value: Any = None,
    multiple_returned_nodes: bool = False,
    at_least_one_returned: bool = True,
) -> Any:
    """
    Having a StudySelection node created on the database, get the connected StudySelection(s)
    """
    connected_node_with_study_value = []
    # get all nodes connected with connected_rel_name
    connected_nodes = getattr(node, connected_rel_name).all()
    if connected_nodes:
        relationships = [
            (_[0], _[1].definition["node_class"])
            for _ in connected_nodes[0].__all_relationships__
        ]
        connected_study_value_rel_name, _ = [
            i_rel for i_rel in relationships if i_rel[1] == type(study_value)
        ][0]
    for connected_node in connected_nodes:
        # get all study_values connected to the connected node

        # pylint: disable=possibly-used-before-assignment
        study_values = getattr(connected_node, connected_study_value_rel_name).all()
        for iter_study_value in study_values:
            # if the connected study_value is the same as the study_value of node
            if iter_study_value == study_value:
                # then take it as connected node
                connected_node_with_study_value.append(connected_node)
    if multiple_returned_nodes:
        return connected_node_with_study_value

    ValidationException.raise_if(
        len(connected_node_with_study_value) > 1,
        msg=f"Returned multiple connected '{connected_rel_name}' nodes and was expecting to match just one.",
    )

    if at_least_one_returned:
        ValidationException.raise_if(
            len(connected_node_with_study_value) == 0,
            msg=f"No connected '{connected_rel_name}' node was found and it was set as mandatory.",
        )
        return connected_node_with_study_value[0]
    return (
        connected_node_with_study_value[0] if connected_node_with_study_value else None
    )


def manage_previous_connected_study_selection_relationships(
    previous_item: Any,
    study_value_node: Any,
    new_item: Any,
    exclude_study_selection_relationships: list[Any] | None = None,
):
    """
    Method for preserving the previous version's connected StudySelection(s) relationships to the current version.
    Take into account that the StudySelection(s) that will be kept are only those
    - those StudySelections that are linked to the study_value_node supplied as a parameter ":param study_value_node:"
    - those StudySelections that are specified as relationship on the NeoModel Class object

    It is possible to exclude StudySelection(s) if they are already kept and can be connected and found by UID on the VO.
    By giving the parameter ":param exclude_study_selection_relationships:" the StudySelections will be excluded.
    This method's purpose is to be maintenance-driven (constantly maintain and define what will be omitted).

    :param previous_item: Any, Previous item from which relationships should be maintained
    :param study_value_node: Any, StudyValue node from which the previous item should be disconnected
    :param new_item: Any, New item to link the existing relationships
    :param exclude_relationships: list[Union[list[Union[str,Any]],Any]] = None,
        Excluded relationships to keep because they are maintained (linked) by its uid
        *  There are two ways to define exclusion:
            * list[Type[StudySelectionNeoModel]: type of the node]
            * list[(str: relationship_name, Type[StudySelectionNeoModel]: type of the node )]
        * For instance:
            * we can define either simply the node type object on exclude_relationships --> [CTTermRoot,...]
            * or we can define the specific relationship exclude_relationships --> [("has_visit_contact_mode", CTTermRoot),...],
            * Both might also be in the same List exclude_relationships --> [("has_visit_contact_mode", CTTermRoot), UnitDefinitionRoot, ...]

    :raises: BusinessLogicException -- An exception is thrown if the previous node is not connected to a StudyValue,
    to ensure that the relationships are preserved.

    :return:
    """
    if not exclude_study_selection_relationships:
        exclude_study_selection_relationships = []
    # ensure that StudyValue will be excluded from being maintained, later will be dropped
    exclude_study_selection_relationships.append(type(study_value_node))
    exclude_study_selection_relationships.append(StudyAction)
    study_selection_relationships = [
        (rel[0], rel[1].definition["node_class"])
        for rel in previous_item.__all_relationships__
        if (
            issubclass(
                rel[1].definition["node_class"],
                (StudySelection, StudyField, type(study_value_node), StudyAction),
            )
        )
    ]
    study_value_rel_name = None
    for rel_name, target_node_type in study_selection_relationships:
        if target_node_type == type(study_value_node):
            study_value_rel_name = rel_name

    study_action_rels = [
        i_rel for i_rel in study_selection_relationships if i_rel[1] == StudyAction
    ]
    # filter just those relationships that we want to maintain, to not appear if rel in exclude_study_selection_relationships
    relationships_to_maintain = [
        i_rel
        for i_rel in study_selection_relationships
        if not (
            i_rel in exclude_study_selection_relationships
            or i_rel[1] in exclude_study_selection_relationships
        )
    ]
    # MAINTAIN non filtered relationships, just for those non filtered relationships nodes with StudyValue connection
    for connected_rel_name, _ in relationships_to_maintain:
        connected_nodes = get_connected_node_by_rel_name_and_study_value(
            node=previous_item,
            connected_rel_name=connected_rel_name,
            study_value=study_value_node,
            multiple_returned_nodes=True,
            at_least_one_returned=False,
        )
        # connect to those connected nodes with same study_value as new_item
        for i_connected_node in connected_nodes:
            getattr(new_item, connected_rel_name).connect(i_connected_node)
    # run ".single()" to confirm that the StudyAction cardinalities are correct.
    for study_action_rel_name, _ in study_action_rels:
        getattr(previous_item, study_action_rel_name).single()
        getattr(new_item, study_action_rel_name).single()
    # DROP StudyValue relationship
    if study_value_rel_name:
        ValidationException.raise_if_not(
            getattr(previous_item, study_value_rel_name).single(),
            msg=f"The modified version of '{previous_item.uid}' of type '{previous_item.__label__}' is not connected to any StudyValue node.",
        )
        getattr(previous_item, study_value_rel_name).disconnect(study_value_node)
