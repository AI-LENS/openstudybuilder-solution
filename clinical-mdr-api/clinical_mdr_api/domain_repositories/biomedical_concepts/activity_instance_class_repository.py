from neomodel import NodeSet, db
from neomodel.sync_.match import (
    Collect,
    Last,
    NodeNameResolver,
    Path,
    RawCypher,
    RelationNameResolver,
)

from clinical_mdr_api.domain_repositories.library_item_repository import (
    LibraryItemRepositoryImplBase,
    _AggregateRootType,
)
from clinical_mdr_api.domain_repositories.models.biomedical_concepts import (
    ActivityInstanceClassRoot,
    ActivityInstanceClassValue,
)
from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.standard_data_model import DatasetClass
from clinical_mdr_api.domain_repositories.neomodel_ext_item_repository import (
    NeomodelExtBaseRepository,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassActivityItemClassRelVO,
    ActivityInstanceClassAR,
    ActivityInstanceClassVO,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClass,
    ActivityInstanceClassWithDataset,
)


class ActivityInstanceClassRepository(  # type: ignore[misc]
    NeomodelExtBaseRepository, LibraryItemRepositoryImplBase[_AggregateRootType]
):
    root_class = ActivityInstanceClassRoot
    value_class = ActivityInstanceClassValue
    return_model = ActivityInstanceClass

    def get_neomodel_extension_query(self) -> NodeSet:
        return (
            ActivityInstanceClassRoot.nodes.traverse(
                "has_latest_value",
                "has_library",
                Path(
                    value="parent_class",
                    optional=True,
                    include_rels_in_return=False,
                ),
                Path(
                    value="parent_class__has_latest_value",
                    optional=True,
                    include_rels_in_return=False,
                ),
            )
            .unique_variables(
                "parent_class",
            )
            .subquery(
                ActivityInstanceClassRoot.nodes.traverse(latest_version="has_version")
                .intermediate_transform(
                    {"rel": {"source": RelationNameResolver("has_version")}},
                    ordering=[
                        RawCypher("toInteger(split(rel.version, '.')[0])"),
                        RawCypher("toInteger(split(rel.version, '.')[1])"),
                        "rel.end_date",
                        "rel.start_date",
                    ],
                )
                .annotate(latest_version=Last(Collect("rel"))),
                ["latest_version"],
                initial_context=[NodeNameResolver("self")],
            )
        )

    def _has_data_changed(
        self, ar: ActivityInstanceClassAR, value: ActivityInstanceClassValue
    ) -> bool:
        if dataset_class := value.has_latest_value.get_or_none():
            dataset_class = dataset_class.maps_dataset_class.get_or_none()

        return (
            ar.activity_instance_class_vo.name != value.name
            or ar.activity_instance_class_vo.order != value.order
            or ar.activity_instance_class_vo.definition != value.definition
            or ar.activity_instance_class_vo.is_domain_specific
            != value.is_domain_specific
            or ar.activity_instance_class_vo.level != value.level
            or (
                ar.activity_instance_class_vo.dataset_class_uid != dataset_class.uid
                if dataset_class
                else None
            )
        )

    def _get_or_create_value(
        self, root: ActivityInstanceClassRoot, ar: ActivityInstanceClassAR
    ) -> ActivityInstanceClassValue:
        for itm in root.has_version.all():
            if not self._has_data_changed(ar, itm):
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
        new_value = ActivityInstanceClassValue(
            name=ar.activity_instance_class_vo.name,
            order=ar.activity_instance_class_vo.order,
            definition=ar.activity_instance_class_vo.definition,
            is_domain_specific=ar.activity_instance_class_vo.is_domain_specific,
            level=ar.activity_instance_class_vo.level,
        )

        self._db_save_node(new_value)

        if ar.activity_instance_class_vo.dataset_class_uid:
            dataset = DatasetClass.nodes.get_or_none(
                uid=ar.activity_instance_class_vo.dataset_class_uid
            )
            root.maps_dataset_class.connect(dataset)

        return new_value

    def generate_uid(self) -> str:
        return ActivityInstanceClassRoot.get_next_free_uid_and_increment_counter()

    def _create_aggregate_root_instance_from_version_root_relationship_and_value(
        self,
        root: ActivityInstanceClassRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ActivityInstanceClassValue,
        **_kwargs,
    ) -> ActivityInstanceClassAR:
        dataset_class = root.maps_dataset_class.get_or_none()
        activity_item_classes = root.has_activity_item_class.all()

        return ActivityInstanceClassAR.from_repository_values(
            uid=root.uid,
            activity_instance_class_vo=ActivityInstanceClassVO.from_repository_values(
                name=value.name,
                order=value.order,
                definition=value.definition,
                is_domain_specific=value.is_domain_specific,
                level=value.level,
                dataset_class_uid=dataset_class.uid if dataset_class else None,
                activity_item_classes=[
                    ActivityInstanceClassActivityItemClassRelVO(
                        uid=activity_item_class.uid,
                        mandatory=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).mandatory,
                        is_adam_param_specific_enabled=activity_item_class.has_activity_instance_class.relationship(
                            root
                        ).is_adam_param_specific_enabled,
                    )
                    for activity_item_class in activity_item_classes
                ],
            ),
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
        )

    def patch_mappings(self, uid: str, dataset_class_uid: str) -> None:
        root = ActivityInstanceClassRoot.nodes.get(uid=uid)
        root.maps_dataset_class.disconnect_all()
        dataset_class = DatasetClass.nodes.get(uid=dataset_class_uid)
        root.maps_dataset_class.connect(dataset_class)

    def get_mapped_datasets(
        self,
        activity_instance_class_uid: str | None = None,
        include_sponsor: bool = True,
    ) -> list[ActivityInstanceClassWithDataset]:
        dataset_label = (
            "DatasetInstance|SponsorModelDatasetInstance"
            if include_sponsor
            else "DatasetInstance"
        )
        query = "MATCH (aicv:ActivityInstanceClassValue)<-[:LATEST]-(aicr:ActivityInstanceClassRoot) "
        if activity_instance_class_uid:
            query += "WHERE aicr.uid=$activity_instance_class_uid"
        query += f"""
            OPTIONAL MATCH (aicr)-[:MAPS_DATASET_CLASS]->(:DatasetClass)-[:HAS_INSTANCE]->(:DatasetClassInstance)<-[:IMPLEMENTS_DATASET_CLASS]-(:{dataset_label})<-[:HAS_INSTANCE]-(d:Dataset)
            OPTIONAL MATCH (aicr)-[:PARENT_CLASS]->{{1,3}}()-[:MAPS_DATASET_CLASS]->(:DatasetClass)
            -[:HAS_INSTANCE]->(:DatasetClassInstance)<-[:IMPLEMENTS_DATASET_CLASS]-(:{dataset_label})<-[:HAS_INSTANCE]-(parent_d:Dataset)
            WITH DISTINCT aicr.uid AS uid, aicv.name AS name, d.uid AS dataset_uid, parent_d.uid AS parent_dataset_uid ORDER BY name, dataset_uid, parent_dataset_uid 
            WITH uid, name, apoc.coll.sort(apoc.coll.toSet(collect(dataset_uid) + collect(parent_dataset_uid))) AS dataset_uids WHERE size(dataset_uids) > 0
            RETURN uid, name, dataset_uids
        """

        results, meta = db.cypher_query(
            query, params={"activity_instance_class_uid": activity_instance_class_uid}
        )

        mapped_datasets = [dict(zip(meta, row)) for row in results]

        output = [
            ActivityInstanceClassWithDataset(
                uid=el["uid"], name=el["name"], datasets=el["dataset_uids"]
            )
            for el in mapped_datasets
        ]

        return output

    def _maintain_parameters(
        self,
        versioned_object: _AggregateRootType,
        root: ActivityInstanceClassRoot,
        value: ActivityInstanceClassValue,
    ) -> None:
        # This method from parent repo is not needed for this repo
        # So we use pass to skip implementation
        pass

    def update_parent(self, parent_uid: str | None, uid: str) -> None:
        root = ActivityInstanceClassRoot.nodes.get(uid=uid)
        root.parent_class.disconnect_all()

        if parent_uid:
            parent = ActivityInstanceClassRoot.nodes.get_or_none(uid=parent_uid)
            root.parent_class.connect(parent)

    def get_parent_class(self, uid: str) -> tuple[str, str] | None:
        root = ActivityInstanceClassRoot.nodes.get_or_none(uid=uid)
        if not root:
            return None

        parent_root = root.parent_class.get_or_none()
        if not parent_root:
            return None

        parent_value = parent_root.has_latest_value.get_or_none()

        return parent_root.uid, parent_value.name
