import copy
from dataclasses import dataclass, fields
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Mapping, MutableSequence, Sequence, cast, overload

from neomodel import NodeSet
from neomodel.exceptions import DoesNotExist
from neomodel.sync_.core import NodeMeta, db
from neomodel.sync_.match import Collect, Last

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.generic_repository import RepositoryImpl
from clinical_mdr_api.domain_repositories.models.concepts import UnitDefinitionRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.dictionary import DictionaryTermRoot
from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrRel,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.project import Project
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_field import (
    StudyArrayField,
    StudyBooleanField,
    StudyField,
    StudyIntField,
    StudyProjectField,
    StudyTextField,
    StudyTimeField,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import (
    StudyDefinitionSnapshot,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_configuration import (
    FieldConfiguration,
    StudyFieldType,
)
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    HighLevelStudyDesignVO,
    StudyDescriptionVO,
    StudyFieldAuditTrailActionVO,
    StudyFieldAuditTrailEntryAR,
    StudyIdentificationMetadataVO,
    StudyInterventionVO,
    StudyPopulationVO,
    StudyStatus,
    StudyVersionMetadataVO,
)
from clinical_mdr_api.models.study_selections.study import (
    StudySoaPreferencesInput,
    StudySubpartAuditTrail,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import (
    CypherQueryBuilder,
    FilterDict,
    FilterOperator,
)
from clinical_mdr_api.services._utils import calculate_diffs
from clinical_mdr_api.services.user_info import UserInfoService
from common import exceptions
from common.config import settings
from common.utils import convert_to_datetime

MAINTAIN_RELATIONSHIPS_FOR_NEW_STUDY_VALUE = {
    "belongs_to_study_parent_part",
    "has_study_activity",
    "has_study_activity_group",
    "has_study_activity_instance",
    "has_study_activity_instruction",
    "has_study_activity_schedule",
    "has_study_activity_subgroup",
    "has_study_arm",
    "has_study_branch_arm",
    "has_study_cohort",
    "has_study_compound",
    "has_study_compound_dosing",
    "has_study_criteria",
    "has_study_design_cell",
    "has_study_disease_milestone",
    "has_study_element",
    "has_study_endpoint",
    "has_study_epoch",
    "has_study_footnote",
    "has_study_objective",
    "has_study_soa_group",
    "has_study_standard_version",
    "has_study_subpart",
    "has_study_visit",
}


def _is_metadata_snapshot_and_status_equal_comparing_study_value_properties(
    current: StudyDefinitionSnapshot, previous: StudyDefinitionSnapshot
) -> bool:
    """
    A convenience function for comparing two snapshot for equality of StudyValue node properties.
    :param current: A StudyDefinitionSnapshot to compare.
    :param previous: Another StudyDefinitionSnapshot to compare.
    :return: True if current == previous (comparing StudyValue node properties), otherwise False
    """
    return (
        current.current_metadata.study_number == previous.current_metadata.study_number
        and current.current_metadata.subpart_id == previous.current_metadata.subpart_id
        and current.current_metadata.study_acronym
        == previous.current_metadata.study_acronym
        and current.current_metadata.study_subpart_acronym
        == previous.current_metadata.study_subpart_acronym
        and current.current_metadata.study_id_prefix
        == previous.current_metadata.study_id_prefix
        and current.current_metadata.description
        == previous.current_metadata.description
        and current.study_status == previous.study_status
        and current.released_metadata == previous.released_metadata
    )


@dataclass(frozen=True)
class _AdditionalClosure:
    root: StudyRoot
    value: StudyValue
    latest_value: ClinicalMdrRel
    latest_draft: VersionRelationship
    latest_released: VersionRelationship | None
    latest_locked: VersionRelationship | None
    previous_snapshot: StudyDefinitionSnapshot


class StudyDefinitionRepositoryImpl(StudyDefinitionRepository, RepositoryImpl):
    def __init__(self, author_id):
        super().__init__()
        self.audit_info.author_id = author_id

    @classmethod
    def _retrieve_draft_study_metadata_snapshot(
        cls,
        latest_draft_value: StudyValue,
        latest_draft_relationship: VersionRelationship,
    ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot:
        draft_metadata_snapshot = cls._study_metadata_snapshot_from_study_value(
            latest_draft_value
        )
        draft_metadata_snapshot = (
            cls._assign_snapshot_ver_properties_from_ver_relationship(
                snapshot=draft_metadata_snapshot,
                ver_relationship=latest_draft_relationship,
            )
        )
        return draft_metadata_snapshot

    @classmethod
    def _retrieve_current_study_metadata_snapshot(
        cls,
        latest_draft_relationship: VersionRelationship,
        draft_snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot,
        latest_locked_relationship: VersionRelationship | None,
        locked_snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot | None,
    ):
        current_metadata_snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot | None

        # some parts of current metadata metadata (those regarding version info) are stored in different way
        # in the underlying DB depending whether current version is draft version or locked
        # so we must retrieve those in different way
        if latest_draft_relationship.end_date is None:
            # in draft we do not need author and info (these are only in db for audit not for business logic)
            # just version timestamp
            current_metadata_snapshot = draft_snapshot
        else:
            # but we need those if current is non-DRAFT (i.e. LOCKED)
            assert latest_locked_relationship is not None
            current_metadata_snapshot = locked_snapshot
        return current_metadata_snapshot

    @classmethod
    def _retrieve_released_study_metadata_snapshot(
        cls, latest_released_value: StudyValue | None, latest_released_relationship
    ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot | None:
        released: StudyDefinitionSnapshot.StudyMetadataSnapshot | None = None
        if latest_released_relationship is not None:
            assert latest_released_value is not None
            released = cls._study_metadata_snapshot_from_study_value(
                latest_released_value
            )
            assert released is not None
            released = cls._assign_snapshot_ver_properties_from_ver_relationship(
                snapshot=released, ver_relationship=latest_released_relationship
            )

        return released

    @classmethod
    def _retrieve_locked_study_metadata_snapshots(
        cls, root: StudyRoot
    ) -> MutableSequence[StudyDefinitionSnapshot.StudyMetadataSnapshot]:
        # now we must retrieve locked versions
        # this is tricky since match gives us the list of values (not relationships)
        # although not very probable however it's possible that two consecutive locked version
        # are actually locked with the same value node
        locked_metadata_snapshots: list[
            StudyDefinitionSnapshot.StudyMetadataSnapshot
        ] = []
        locked_value_node: StudyValue
        # so we get locked value nodes first
        # however there is a problem. neomodel returns them many times if there are multiple relationship instances
        # between them. There for we must remember ids of processed nodes, to skip subsequent processing of the same
        # node.
        processed_nodes = set()
        for locked_value_node in root.has_version.match(
            status=StudyStatus.LOCKED.value
        ):
            # then for every value we get has_version_relationship which are LOCKED
            if locked_value_node.element_id in processed_nodes:
                # we skip processing in case we already have it processed
                continue
            # if we haven't processed it yet we process (and store it as processed)
            processed_nodes.add(locked_value_node.element_id)

            # here goes the real processing
            has_version_relationship_instance: VersionRelationship
            for has_version_relationship_instance in root.has_version.all_relationships(
                locked_value_node
            ):
                if has_version_relationship_instance.status == StudyStatus.LOCKED.value:
                    locked = cls._study_metadata_snapshot_from_study_value(
                        locked_value_node
                    )
                    locked = cls._assign_snapshot_ver_properties_from_ver_relationship(
                        snapshot=locked,
                        ver_relationship=has_version_relationship_instance,
                    )
                    locked_metadata_snapshots.append(locked)

        # now we have all locked metadata snapshot in locked_metadata_snapshots list. However in indeterminate order
        # and aggregate want them chronological. So we need to sort the list by version_timestamp
        locked_metadata_snapshots.sort(
            key=lambda _: cast(datetime, _.version_timestamp)
        )

        return locked_metadata_snapshots

    @classmethod
    def _retrieve_all_snapshots_from_cypher_query_result(
        cls, result_set: list[dict[Any, Any]], deleted: bool = False
    ) -> list[StudyDefinitionSnapshot]:
        """
        Function maps the result of the cypher query which is list of dictionaries into
        the list of domain layer objects called StudyDefinitionSnapshot.
        It uses StudyDefinitionRepositoryImpl._study_metadata_snapshot_from_cypher_res to create specific members
        of StudyDefinitionSnapshot that are called StudyMetadataSnapshots.
        :param result_set:
        :return list[StudyDefinitionSnapshot]:
        """
        snapshots: list[StudyDefinitionSnapshot] = []
        for study in result_set:
            current_metadata_snapshot = cls._study_metadata_snapshot_from_cypher_res(
                study["current_metadata"]
            )
            released_metadata_snapshot = cls._study_metadata_snapshot_from_cypher_res(
                study["released_metadata"]
            )
            draft_metadata_snapshot = cls._study_metadata_snapshot_from_cypher_res(
                study["draft_metadata"]
            )
            locked_metadata_versions = (
                study["locked_metadata_versions"]["locked_metadata_array"]
                if study["locked_metadata_versions"] is not None
                else []
            )
            locked_metadata_snapshots = [
                cls._study_metadata_snapshot_from_cypher_res(locked_metadata)
                for locked_metadata in locked_metadata_versions
            ]
            snapshot = StudyDefinitionSnapshot(
                deleted=deleted,
                current_metadata=current_metadata_snapshot,
                released_metadata=released_metadata_snapshot,
                draft_metadata=draft_metadata_snapshot,
                locked_metadata_versions=locked_metadata_snapshots,
                uid=study["uid"],
                study_parent_part_uid=study["study_parent_part_uid"],
                study_subpart_uids=study["study_subpart_uids"],
                study_status=(
                    study["study_status"] if not deleted else StudyStatus.DELETED.value
                ),
            )
            snapshots.append(snapshot)
        return snapshots

    @classmethod
    def _retrieve_snapshot(
        cls,
        item: StudyRoot,
        study_value_version: str | None = None,
    ) -> tuple[StudyDefinitionSnapshot, _AdditionalClosure]:
        root: StudyRoot = item
        specific_study_value: StudyValue | None = None
        specific_study_value_relationship: VersionRelationship | None = None

        if study_value_version:
            study_value_and_root = (
                StudyValue.nodes.filter(
                    **{
                        "has_version|version": study_value_version,
                        "has_version__uid": root.uid,
                    }
                )
                .intermediate_transform({"studyvalue": {"source": "studyvalue"}})
                .annotate(study_value=Last(Collect("studyvalue", distinct=True)))
                .get_or_none()
            )
            exceptions.NotFoundException.raise_if_not(
                study_value_and_root,
                "Study version",
                study_value_version,
                "value",
            )
            study_value = study_value_and_root

            assert isinstance(study_value, StudyValue)
            specific_study_value = study_value
            # To be updated to below if the HAS_VERSION status:draft relationship is removed
            # specific_study_value_relationship = root.has_version.relationship(
            #     specific_study_value
            # )
            specific_study_value_relationship = [
                ith
                for ith in root.has_version.all_relationships(specific_study_value)
                if ith.status == "RELEASED"
            ][0]

        latest_value: StudyValue = root.latest_value.single()
        latest_value_relationship: VersionRelationship = root.latest_value.relationship(
            latest_value
        )

        latest_draft_value: StudyValue = root.latest_draft.single()
        latest_draft_relationship: VersionRelationship = root.latest_draft.relationship(
            latest_draft_value
        )

        latest_released_value: StudyValue | None = root.latest_released.single()
        latest_released_relationship: VersionRelationship | None = (
            None
            if latest_released_value is None
            else root.latest_released.relationship(latest_released_value)
        )

        latest_locked_value: StudyValue | None = root.latest_locked.single()
        latest_locked_relationship: VersionRelationship | None = (
            None
            if latest_locked_value is None
            else root.latest_locked.relationship(latest_locked_value)
        )

        draft_metadata_snapshot = cls._retrieve_draft_study_metadata_snapshot(
            latest_draft_value=latest_draft_value,
            latest_draft_relationship=latest_draft_relationship,
        )

        released_metadata_snapshot = cls._retrieve_released_study_metadata_snapshot(
            latest_released_value=latest_released_value,
            latest_released_relationship=latest_released_relationship,
        )

        specific_metadata_snapshot = cls._retrieve_released_study_metadata_snapshot(
            latest_released_value=specific_study_value,
            latest_released_relationship=specific_study_value_relationship,
        )

        locked_metadata_snapshots = cls._retrieve_locked_study_metadata_snapshots(
            root=root
        )

        current_metadata_snapshot = cls._retrieve_current_study_metadata_snapshot(
            latest_draft_relationship=latest_draft_relationship,
            draft_snapshot=draft_metadata_snapshot,
            latest_locked_relationship=latest_locked_relationship,
            locked_snapshot=(
                locked_metadata_snapshots[-1] if latest_locked_relationship else None
            ),
        )

        # now we just build snapshot of the aggregate instance

        snapshot = StudyDefinitionSnapshot(
            deleted=False,
            current_metadata=current_metadata_snapshot,
            draft_metadata=draft_metadata_snapshot,
            released_metadata=released_metadata_snapshot,
            specific_metadata=specific_metadata_snapshot,
            locked_metadata_versions=locked_metadata_snapshots,
            uid=root.uid,
            study_parent_part_uid=cls._get_parent_part_uid(root.uid),
            study_subpart_uids=cls._get_subpart_uids(root.uid),
            # since we do not have study definition status stored directly in DB we need to derive it
            # from information we have directly accessible
            study_status=(
                StudyStatus.DRAFT.value
                if latest_draft_relationship.end_date is None
                else StudyStatus.LOCKED.value
            ),
        )
        # and return the snapshot and closure data which may be needed when the instance is saved later
        return snapshot, _AdditionalClosure(
            root=root,
            value=latest_value,
            latest_value=latest_value_relationship,
            latest_draft=latest_draft_relationship,
            latest_released=latest_released_relationship,
            latest_locked=latest_locked_relationship,
            previous_snapshot=copy.deepcopy(snapshot),
        )

    @staticmethod
    def _get_parent_part_uid(uid: str) -> str | None:
        rs = db.cypher_query(
            """
                MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_SUBPART]->(sub_sv:StudyValue)<-[:LATEST]-(sub_sr:StudyRoot {uid: $uid})
                RETURN sr.uid
            """,
            params={"uid": uid},
        )

        return rs[0][0][0] if rs[0] else None

    @staticmethod
    def _get_subpart_uids(uid: str) -> list[str]:
        rs = db.cypher_query(
            """
                MATCH (sr:StudyRoot {uid: $uid})-[:LATEST]->(sv:StudyValue)-[:HAS_STUDY_SUBPART]->(sub_sv:StudyValue)<-[:LATEST]-(sub_sr:StudyRoot)
                WHERE NOT EXISTS((sub_sr)-[:AUDIT_TRAIL]->(:StudyAction:`Delete`)-[:BEFORE]->(sub_sv))
                RETURN sub_sr.uid
            """,
            params={"uid": uid},
        )

        return [uid[0] for uid in rs[0]]

    @staticmethod
    def _ensure_transaction() -> None:
        """ensures a Neomodel database transaction is active"""

        if getattr(db, "_active_transaction", None) is None:
            raise SystemError(
                "Must be called inside an active Neomodel database transaction to retrieve StudyDefinition for update."
            )

    def _retrieve_snapshot_by_uid(
        self,
        uid: str,
        for_update: bool,
        study_value_version: str | None = None,
    ) -> tuple[StudyDefinitionSnapshot | None, Any]:
        if for_update:
            self._ensure_transaction()
            acquire_write_lock_study_value(uid)

            # we should be able to return deleted studies
            # but it should not be possible to be edited
            exceptions.BusinessLogicException.raise_if(
                self.check_if_study_is_deleted(study_uid=uid),
                msg=f"Study with UID '{uid}' is deleted.",
            )

        root: StudyRoot

        try:
            root = StudyRoot.nodes.get(uid=uid)
        except DoesNotExist:
            return None, None

        snapshot, model_data = self._retrieve_snapshot(
            item=root,
            study_value_version=study_value_version,
        )

        return snapshot, (model_data if for_update else None)

    def _save(
        self,
        snapshot: StudyDefinitionSnapshot,
        additional_closure: Any,
        is_subpart_relationship_update: bool = False,
    ) -> None:
        self._ensure_transaction()  # raises an error if we are not inside transaction

        assert isinstance(
            additional_closure, _AdditionalClosure
        )  # this should always hold here

        # convenience variables (those not used are commented out, however may become useful later)
        current_snapshot: StudyDefinitionSnapshot = snapshot
        previous_snapshot: StudyDefinitionSnapshot = (
            additional_closure.previous_snapshot
        )
        previous_value: StudyValue = additional_closure.value
        latest_draft: VersionRelationship = additional_closure.latest_draft
        latest_released: VersionRelationship | None = additional_closure.latest_released
        latest_locked: VersionRelationship | None = additional_closure.latest_locked
        root: StudyRoot = additional_closure.root
        date = datetime.now(timezone.utc)

        # we do nothing if nothing changed
        if previous_snapshot == current_snapshot and not is_subpart_relationship_update:
            return

        # generate :StudyAction:Delete node
        if current_snapshot.deleted:
            self._generate_study_value_audit_node(
                study_root_node=root,
                study_value_node_after=None,
                study_value_node_before=previous_value,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=date,
            )
            return

        # some assertions about what and how can things be or change (current implementation is built on those
        # assumptions and may break if they not hold)
        assert (
            current_snapshot.current_metadata is not None
        )  # there must be some current value
        assert previous_snapshot.current_metadata  # in previous snapshot as well
        # there are only two possible permanent current states of the aggregate
        assert current_snapshot.study_status in (
            StudyStatus.DRAFT.value,
            StudyStatus.LOCKED.value,
        )
        assert (
            current_snapshot.uid == previous_snapshot.uid
        )  # uid cannot change (something is very wrong if it does)

        # locked metadata which had been persisted before do not change
        if (
            len(current_snapshot.locked_metadata_versions) > 0
            and len(previous_snapshot.locked_metadata_versions) > 0
        ):
            from dataclasses import asdict

            for k, value in asdict(
                current_snapshot.locked_metadata_versions[0]
            ).items():
                version1 = getattr(previous_snapshot.locked_metadata_versions[0], k)
                assert value == version1
            assert asdict(current_snapshot.locked_metadata_versions[0]) == asdict(
                previous_snapshot.locked_metadata_versions[0]
            )
        assert (
            current_snapshot.locked_metadata_versions[
                0 : len(previous_snapshot.locked_metadata_versions)
            ]
            == previous_snapshot.locked_metadata_versions
        )

        # first we maintain latest_value (possibly creating new value node)
        expected_latest_value = self._maintain_latest_value_and_relationship_on_save(
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
            previous_value=previous_value,
            root=root,
            date=date,
            is_subpart_relationship_update=is_subpart_relationship_update,
        )

        # now we maintain all types of relationship we have in DB to the study.

        self._maintain_latest_draft_relationship_on_save(
            expected_latest_value=expected_latest_value,
            latest_draft_relationship=latest_draft,
            root=root,
            current_snapshot=current_snapshot,
        )
        self._maintain_latest_locked_relationship_on_save(
            expected_latest_value=expected_latest_value,
            latest_locked=latest_locked,
            previous_snapshot=previous_snapshot,
            root=root,
            current_snapshot=current_snapshot,
        )
        self._maintain_latest_released_relationship_on_save(
            current_snapshot=current_snapshot,
            latest_released=latest_released,
            previous_snapshot=previous_snapshot,
            root=root,
            previous_value=previous_value,
            expected_latest_value=expected_latest_value,
        )
        self._maintain_has_version_relationship_on_save(
            expected_latest_value=expected_latest_value,
            root=root,
            current_snapshot=current_snapshot,
            previous_snapshot=previous_snapshot,
            previous_latest_value=previous_value,
        )

        # Next, persist and maintain the study fields as nodes in the graph.
        self._maintain_study_project_field_relationship(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        self._maintain_study_fields_relationships(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        self._maintain_study_array_fields_relationships(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        self._maintain_study_registry_id_fields_relationships(
            root,
            previous_snapshot,
            current_snapshot,
            previous_value,
            expected_latest_value,
            date,
        )
        for rel in MAINTAIN_RELATIONSHIPS_FOR_NEW_STUDY_VALUE:
            self._maintain_study_relationship_on_save(
                rel, expected_latest_value, previous_value
            )
        self._maintain_study_pref_time_unit_relationship_on_save(
            expected_latest_value=expected_latest_value, previous_value=previous_value
        )
        self._maintain_study_soa_preferences_relationship_on_save(
            expected_latest_value=expected_latest_value, previous_value=previous_value
        )

    def _maintain_study_relationship_on_save(
        self,
        relation_name: str,
        expected_latest_value: StudyValue,
        previous_value: StudyValue,
    ):
        # check if new value node is created
        if expected_latest_value is not previous_value:
            study_selection_nodes = getattr(previous_value, relation_name).all()
            if relation_name not in MAINTAIN_RELATIONSHIPS_FOR_NEW_STUDY_VALUE:
                # remove the relation from the old value node
                getattr(previous_value, relation_name).disconnect_all()
            # add the relation to the new node
            for study_selection_node in study_selection_nodes:
                if relation_name in [
                    "has_study_subpart",
                    "belongs_to_study_parent_part",
                ]:
                    if study_selection_node.latest_value.single():
                        getattr(expected_latest_value, relation_name).connect(
                            study_selection_node
                        )
                else:
                    getattr(expected_latest_value, relation_name).connect(
                        study_selection_node
                    )

    def _maintain_study_pref_time_unit_relationship_on_save(
        self, expected_latest_value: StudyValue, previous_value: StudyValue
    ):
        # check if new value node is created
        if expected_latest_value is not previous_value:
            # remove the relation from the old value node
            preferred_time_unit_node = previous_value.has_time_field.get_or_none(
                field_name=settings.study_field_preferred_time_unit_name
            )
            soa_preferred_time_unit_node = previous_value.has_time_field.get_or_none(
                field_name=settings.study_field_soa_preferred_time_unit_name
            )
            if preferred_time_unit_node is not None:
                # add the relation to the new node
                expected_latest_value.has_time_field.connect(preferred_time_unit_node)

            if soa_preferred_time_unit_node is not None:
                # add the relation to the new node
                expected_latest_value.has_time_field.connect(
                    soa_preferred_time_unit_node
                )

    def _maintain_study_soa_preferences_relationship_on_save(
        self, expected_latest_value: StudyValue, previous_value: StudyValue
    ):
        # if new value node is created
        if expected_latest_value is not previous_value:
            nodes = previous_value.has_boolean_field.filter(
                field_name__in=settings.study_soa_preferences_fields
            )

            for node in nodes:
                # add the relation to the new node
                expected_latest_value.has_boolean_field.connect(node)

    def _maintain_latest_value_and_relationship_on_save(
        self,
        current_snapshot: StudyDefinitionSnapshot,
        previous_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        root: StudyRoot,
        date: datetime,
        is_subpart_relationship_update: bool = False,
    ):
        assert (
            current_snapshot.current_metadata is not None
        )  # sth must be very wrong if does not hold
        assert (
            previous_snapshot.current_metadata is not None
        )  # sth must be very wrong if does not hold
        # first we need to know whether we have to create new value node
        # i.e. whether there are changes in other but version related metadata
        # if there are none we do not need to maintain anything and we expect the new latest value be exactly the same
        # node as the previous
        expected_latest_value = previous_value

        if (
            not _is_metadata_snapshot_and_status_equal_comparing_study_value_properties(
                current_snapshot,
                previous_snapshot,
                # we don't wan't to create new StudyValue node if we've just LOCKED a Study
            )
            and current_snapshot.study_status != StudyStatus.LOCKED.value
        ) or is_subpart_relationship_update:
            # we need a new node (for a new value)
            expected_latest_value = self._study_value_from_study_metadata_snapshot(
                current_snapshot.current_metadata
            )
            expected_latest_value.save()

            # in this case we also need to reconnect LATEST relationship
            root.latest_value.reconnect(
                old_node=previous_value, new_node=expected_latest_value
            )

            self._generate_study_value_audit_node(
                study_root_node=root,
                study_value_node_after=expected_latest_value,
                study_value_node_before=previous_value,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=date,
            )
        return expected_latest_value

    def _maintain_latest_released_relationship_on_save(
        self,
        current_snapshot,
        latest_released,
        previous_snapshot,
        root,
        previous_value,
        expected_latest_value,
    ):
        if current_snapshot.study_status == StudyStatus.DRAFT.value:
            study_value_node_to_connect = previous_value
        else:
            study_value_node_to_connect = expected_latest_value
        # now we maintain LATEST_RELEASED relationship
        # the maintenance is needed only if there is some change in released_metadata
        if current_snapshot.released_metadata != previous_snapshot.released_metadata:
            # if released_metadata have been removed (is None) we just need to close LATEST_RELEASE (if it's open)
            # (i.e. set end_date if not set)
            if current_snapshot.released_metadata is None:
                assert latest_released is not None
                if latest_released.end_date is None:
                    latest_released.end_date = (
                        current_snapshot.current_metadata.version_timestamp
                    )
                    latest_released.save()
            else:
                # if we have some new released_metadata we either initialize LATEST_RELEASED relationship (if there is
                # none) or update and reconnect existing if there is one
                if latest_released is None:  # initialize LATEST_RELEASED
                    version_properties = {
                        "start_date": current_snapshot.released_metadata.version_timestamp,
                        "status": StudyStatus.RELEASED.value,
                        "author_id": self.audit_info.author_id,
                        "version": current_snapshot.released_metadata.version_number,
                        "change_description": current_snapshot.released_metadata.version_description,
                    }
                    root.latest_released.connect(
                        study_value_node_to_connect, properties=version_properties
                    )
                    root.has_version.connect(
                        study_value_node_to_connect, properties=version_properties
                    )
                else:  # update and reconnect goes below
                    latest_released.start_date = (
                        current_snapshot.released_metadata.version_timestamp
                    )
                    latest_released.change_description = (
                        current_snapshot.released_metadata.version_description
                    )
                    latest_released.author_id = self.audit_info.author_id
                    latest_released.version = (
                        current_snapshot.released_metadata.version_number
                    )
                    latest_released.end_date = None
                    latest_released.save()
                    root.has_version.connect(
                        study_value_node_to_connect,
                        properties={
                            "start_date": latest_released.start_date,
                            "status": latest_released.status,
                            "author_id": latest_released.author_id,
                            "version": latest_released.version,
                            "change_description": latest_released.change_description,
                        },
                    )
                    root.latest_released.reconnect(
                        old_node=latest_released.end_node(),
                        new_node=study_value_node_to_connect,
                    )

    def _maintain_has_version_relationship_on_save(
        self,
        expected_latest_value: StudyValue,
        root: StudyRoot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_snapshot: StudyDefinitionSnapshot,
        previous_latest_value: StudyValue,
    ):
        assert (
            current_snapshot.current_metadata is not None
        )  # something must be very wrong if this not hold
        # we maintain HAS_VERSION which means two actions:
        # 1. close the instance of the relation which is open and connected to current value
        # 2. create new instance of the relation connected to expected_latest_value (which may be new one or the same)

        # We want to maintain HAS_VERSION if we've created a new StudyValue node or StudyStatus is different
        # for going from DRAFT -> LOCKED we are not creating a new StudyValue node
        if (
            expected_latest_value != previous_latest_value
            or current_snapshot.study_status != previous_snapshot.study_status
        ):
            # here goes step 1 (closing the old HAS_VERSION instance)
            has_version_relationship: VersionRelationship
            for has_version_relationship in root.has_version.all_relationships(
                previous_latest_value
            ):
                if has_version_relationship.end_date is None:
                    has_version_relationship.end_date = (
                        current_snapshot.current_metadata.version_timestamp
                    )
                    has_version_relationship.save()
            # and step 2 (creating a new instance)
            root.has_version.connect(
                expected_latest_value,
                properties={
                    "start_date": current_snapshot.current_metadata.version_timestamp,
                    "status": current_snapshot.study_status,
                    "author_id": self.audit_info.author_id,
                    "version": current_snapshot.current_metadata.version_number,
                    "change_description": current_snapshot.current_metadata.version_description,
                },
            )

    def _maintain_latest_locked_relationship_on_save(
        self,
        expected_latest_value: StudyValue,
        latest_locked: VersionRelationship | None,
        previous_snapshot: StudyDefinitionSnapshot,
        root: StudyRoot,
        current_snapshot: StudyDefinitionSnapshot,
    ):
        assert (
            current_snapshot.current_metadata is not None
        )  # something must be very wrong if this not hold
        # if the study is in LOCKED state then we need to update or initialize LATEST_LOCKED relationship
        # we do not need to do anything otherwise (does not affect LATEST_LOCKED)
        if len(current_snapshot.locked_metadata_versions) != len(
            previous_snapshot.locked_metadata_versions
        ):
            # this is not exactly forbidden (to lock more than once in single transaction),
            # however not needed currently and hence not implemented (at least not tested for this case)
            # i.e. we support exactly one new LOCKED version
            if (
                len(current_snapshot.locked_metadata_versions)
                - len(previous_snapshot.locked_metadata_versions)
                != 1
            ):
                raise NotImplementedError(
                    f"Study {current_snapshot.uid}: locking more than once in the same request not supported (yet?)."
                )

            # update and reconnect LATEST_LOCKED relationship if there is one
            if latest_locked is not None:
                if current_snapshot.current_metadata.version_timestamp is None:
                    raise ValueError("Version timestamp must not be None.")

                latest_locked.start_date = (
                    current_snapshot.current_metadata.version_timestamp
                )
                latest_locked.author_id = self.audit_info.author_id
                latest_locked.change_description = (
                    current_snapshot.current_metadata.version_description
                )
                latest_locked.version = len(current_snapshot.locked_metadata_versions)
                latest_locked.save()
                root.latest_locked.reconnect(
                    old_node=latest_locked.end_node(), new_node=expected_latest_value
                )
            else:
                # we have to initialize LATEST_LOCKED relationship if there is none
                root.latest_locked.connect(
                    expected_latest_value,
                    properties={
                        "start_date": current_snapshot.current_metadata.version_timestamp,
                        "status": current_snapshot.study_status,
                        "author_id": self.audit_info.author_id,
                        "change_description": current_snapshot.current_metadata.version_description,
                        "version": len(current_snapshot.locked_metadata_versions),
                    },
                )

    def _maintain_latest_draft_relationship_on_save(
        self,
        expected_latest_value: StudyValue,
        latest_draft_relationship: VersionRelationship,
        root: StudyRoot,
        current_snapshot: StudyDefinitionSnapshot,
    ) -> None:
        assert (
            current_snapshot.current_metadata is not None
        )  # this should always hold (something is very wrong if not)
        # if this is study in DRAFT state we need to update LATEST_DRAFT attributes and possibly reconnect
        if current_snapshot.study_status == StudyStatus.DRAFT.value:
            # we need to update attributes of latest DRAFT
            if current_snapshot.current_metadata.version_timestamp is None:
                raise ValueError("Version timestamp must not be None.")

            latest_draft_relationship.start_date = (
                current_snapshot.current_metadata.version_timestamp
            )
            latest_draft_relationship.author_id = self.audit_info.author_id
            latest_draft_relationship.end_date = None
            latest_draft_relationship.save()
            root.latest_draft.reconnect(
                old_node=latest_draft_relationship.end_node(),
                new_node=expected_latest_value,
            )
        else:  # if it's not in DRAFT (anymore)
            # then we may need to close (set end date) on LATEST_DRAFT (if it's not already closed)
            if latest_draft_relationship.end_date is None:
                latest_draft_relationship.end_date = (
                    current_snapshot.current_metadata.version_timestamp
                )
                latest_draft_relationship.save()

    def _maintain_study_project_field_relationship(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        if (
            curr_metadata.project_number != prev_metadata.project_number
            or previous_value is not expected_latest_value
        ):
            project_node = Project.nodes.get(
                project_number=curr_metadata.project_number
            )

            # assigning Project to newly created StudyValue node
            study_project_field = StudyProjectField()
            study_project_field.save()
            study_project_field.has_field.connect(project_node)
            expected_latest_value.has_project.connect(study_project_field)

            prev_study_project_field = previous_value.has_project.get_or_none()
            if (
                prev_study_project_field is not None
                and previous_value is expected_latest_value
            ):
                expected_latest_value.has_project.disconnect(prev_study_project_field)
            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_after=study_project_field,
                study_field_node_before=prev_study_project_field,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=date,
            )

    def _get_associated_ct_term_root_node(
        self, term_uid: str, study_field_name: str, is_dictionary_term: bool = False
    ) -> CTTermRoot | DictionaryTermRoot:
        if not is_dictionary_term:
            query = """
                MATCH (term_root:CTTermRoot {uid: $uid})-[:HAS_NAME_ROOT]->()-[:LATEST_FINAL]->()
                RETURN term_root
                """
        else:
            query = """
                MATCH (dictionary_term_root:DictionaryTermRoot {uid: $uid})-[:LATEST_FINAL]->()
                RETURN dictionary_term_root
                """
        result, _ = db.cypher_query(query, {"uid": term_uid}, resolve_objects=True)
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0]
        raise exceptions.ValidationException(
            msg=f"{'DictionaryTerm' if is_dictionary_term else 'CTTerm'} with UID '{term_uid}' doesn't exist."
            f"Please check if the CT data was properly loaded for the following StudyField '{study_field_name}'."
        )

    def _get_previous_study_field_node(
        self,
        config_item,
        study_root,
        study_field_name,
        prev_study_field_value,
        prev_study_field_null_value_code,
    ):
        null_value_code = (
            None if prev_study_field_value else prev_study_field_null_value_code
        )
        prev_study_field_node = None
        if config_item.study_field_data_type == StudyFieldType.TEXT:
            prev_study_field_node = (
                StudyTextField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        elif config_item.study_field_data_type == StudyFieldType.BOOL:
            prev_study_field_node = (
                StudyBooleanField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        elif config_item.study_field_data_type == StudyFieldType.TIME:
            prev_study_field_node = (
                StudyTimeField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        elif config_item.study_field_data_type == StudyFieldType.INT:
            prev_study_field_node = (
                StudyIntField.get_specific_field_currently_used_in_study(
                    study_uid=study_root.uid,
                    field_name=study_field_name,
                    value=prev_study_field_value,
                    null_value_code=null_value_code,
                )
            )
        return prev_study_field_node

    def _get_or_create_study_field_node(
        self,
        study_field: type,
        study_root: StudyRoot,
        study_field_name: str,
        study_field_value: Any,
        term_root_node: CTTermRoot | DictionaryTermRoot | None,
        null_value_code: str | None = None,
        to_delete: bool = False,
    ):
        study_field_node = study_field.get_specific_field_currently_used_in_study(
            study_uid=study_root.uid,
            field_name=study_field_name,
            value=study_field_value,
            null_value_code=null_value_code,
        )
        if study_field_node is None or to_delete:
            study_field_node = study_field.create(
                {
                    "value": study_field_value,
                    "field_name": study_field_name,
                }
            )[0]
        if term_root_node:
            study_field_node.has_type.connect(term_root_node)
        if null_value_code:
            null_value_reason_node = self._get_associated_ct_term_root_node(
                term_uid=null_value_code,
                study_field_name="Null Flavour",
            )

            study_field_node.has_reason_for_null_value.connect(null_value_reason_node)
        return study_field_node

    def _maintain_study_fields_relationships(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        for config_item in FieldConfiguration.default_field_config():
            if (
                config_item.study_field_grouping == "ver_metadata"
                or config_item.study_field_data_type
                not in [
                    StudyFieldType.TEXT,
                    StudyFieldType.BOOL,
                    StudyFieldType.TIME,
                    StudyFieldType.INT,
                ]
            ):
                continue

            study_field_value = getattr(
                curr_metadata, config_item.study_field_name
            )  # current field value
            prev_study_field_value = getattr(
                prev_metadata, config_item.study_field_name
            )  # previous field value
            study_field_name = config_item.study_field_name_api  # field name
            if config_item.study_field_null_value_code is not None:
                prev_study_field_null_value_code = getattr(
                    prev_metadata, config_item.study_field_null_value_code
                )  # previous null value code
                study_field_null_value_code = getattr(
                    curr_metadata, config_item.study_field_null_value_code
                )  # current null value code
            else:
                prev_study_field_null_value_code = None
                study_field_null_value_code = None

            if (
                study_field_value != prev_study_field_value
                or previous_value is not expected_latest_value
                or prev_study_field_null_value_code != study_field_null_value_code
            ):
                prev_study_field_node = self._get_previous_study_field_node(
                    config_item=config_item,
                    study_root=study_root,
                    study_field_name=study_field_name,
                    prev_study_field_value=prev_study_field_value,
                    prev_study_field_null_value_code=prev_study_field_null_value_code,
                )
                study_field_node = None
                # check if the study field needs to be deleted
                to_delete = False
                if study_field_value is None and study_field_null_value_code is None:
                    if study_field_value is None and prev_study_field_value is not None:
                        study_field_value = prev_study_field_value
                        to_delete = True
                    elif (
                        study_field_null_value_code is None
                        and prev_study_field_null_value_code is not None
                    ):
                        study_field_null_value_code = prev_study_field_null_value_code
                        to_delete = True
                if (
                    study_field_value is not None
                    or study_field_null_value_code is not None
                ):
                    node_uid = None
                    if config_item.configured_codelist_uid:
                        node_uid = study_field_value
                    elif config_item.study_field_data_type == StudyFieldType.BOOL:
                        node_uid = (
                            settings.ct_uid_boolean_yes
                            if study_field_value
                            else settings.ct_uid_boolean_no
                        )
                    elif config_item.configured_term_uid:
                        node_uid = config_item.configured_term_uid
                    if node_uid:
                        ct_term_root_node = self._get_associated_ct_term_root_node(
                            term_uid=node_uid,
                            study_field_name=study_field_name,
                            is_dictionary_term=config_item.is_dictionary_term,
                        )
                    else:
                        ct_term_root_node = None

                    if study_field_value is not None:
                        if config_item.study_field_data_type == StudyFieldType.TEXT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTextField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_text_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.BOOL:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyBooleanField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_boolean_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.TIME:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTimeField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_time_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.INT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyIntField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_int_field.connect(
                                    study_field_node
                                )

                    elif study_field_null_value_code is not None:
                        if config_item.study_field_data_type == StudyFieldType.TEXT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTextField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_text_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.BOOL:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyBooleanField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_boolean_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.TIME:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyTimeField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_time_field.connect(
                                    study_field_node
                                )
                        elif config_item.study_field_data_type == StudyFieldType.INT:
                            study_field_node = self._get_or_create_study_field_node(
                                study_field=StudyIntField,
                                study_root=study_root,
                                study_field_name=study_field_name,
                                study_field_value=study_field_value,
                                term_root_node=ct_term_root_node,
                                null_value_code=study_field_null_value_code,
                                to_delete=to_delete,
                            )
                            if not to_delete:
                                expected_latest_value.has_int_field.connect(
                                    study_field_node
                                )
                if (
                    prev_study_field_node is not None
                    and (prev_study_field_node != study_field_node)
                    and previous_value is expected_latest_value
                ):
                    if config_item.study_field_data_type == StudyFieldType.TEXT:
                        expected_latest_value.has_text_field.disconnect(
                            prev_study_field_node
                        )
                    elif config_item.study_field_data_type == StudyFieldType.BOOL:
                        expected_latest_value.has_boolean_field.disconnect(
                            prev_study_field_node
                        )
                    elif config_item.study_field_data_type == StudyFieldType.TIME:
                        expected_latest_value.has_time_field.disconnect(
                            prev_study_field_node
                        )
                    elif config_item.study_field_data_type == StudyFieldType.INT:
                        expected_latest_value.has_int_field.disconnect(
                            prev_study_field_node
                        )
                if study_field_node != prev_study_field_node:
                    self._generate_study_field_audit_node(
                        study_root_node=study_root,
                        study_field_node_after=study_field_node,
                        study_field_node_before=prev_study_field_node,
                        change_status=None,
                        author_id=self.audit_info.author_id,
                        date=date,
                        to_delete=to_delete,
                    )

    def _maintain_study_array_fields_relationships(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        for config_item in [
            item
            for item in FieldConfiguration.default_field_config()
            if item.study_field_data_type == StudyFieldType.CODELIST_MULTISELECT
        ]:
            study_array_field_value = getattr(
                curr_metadata, config_item.study_field_name
            )  # current field value
            prev_study_array_field_value = getattr(
                prev_metadata, config_item.study_field_name
            )  # previous field value
            study_array_field_name = config_item.study_field_name_api  # field name
            if config_item.study_field_null_value_code is not None:
                prev_study_array_field_null_value_code = getattr(
                    prev_metadata, config_item.study_field_null_value_code
                )  # previous null value code
                study_array_field_null_value_code = getattr(
                    curr_metadata, config_item.study_field_null_value_code
                )  # current null value code
            else:
                study_array_field_null_value_code = None
                prev_study_array_field_null_value_code = None
            is_c_code_field = (
                config_item.configured_codelist_uid
            )  # is this codelist field

            if (
                study_array_field_value != prev_study_array_field_value
                or previous_value is not expected_latest_value
                or prev_study_array_field_null_value_code
                != study_array_field_null_value_code
            ):
                prev_study_array_field_node = (
                    StudyArrayField.get_specific_field_currently_used_in_study(
                        study_uid=study_root.uid,
                        field_name=study_array_field_name,
                        value=prev_study_array_field_value,
                    )
                )

                study_array_field_node = None
                # check if the study field needs to be deleted
                to_delete = False
                if (
                    not study_array_field_value
                    and study_array_field_null_value_code is None
                ):
                    if (
                        not (
                            study_array_field_value
                            or study_array_field_null_value_code is not None
                        )
                        and prev_study_array_field_value
                    ):
                        study_array_field_value = prev_study_array_field_value
                        to_delete = True
                    elif (
                        not (
                            not study_array_field_value
                            and study_array_field_null_value_code is not None
                        )
                        and prev_study_array_field_null_value_code is not None
                    ):
                        study_array_field_null_value_code = (
                            prev_study_array_field_null_value_code
                        )
                        to_delete = True

                if (
                    study_array_field_value
                    or study_array_field_null_value_code is not None
                ):
                    ct_term_root_nodes = []
                    # we can't link CTTermRoot for these nodes as they are not valid codelists at the moment
                    if is_c_code_field or config_item.is_dictionary_term:
                        if study_array_field_value is not None:
                            for study_array_value in study_array_field_value:
                                ct_term_root_node = self._get_associated_ct_term_root_node(
                                    term_uid=study_array_value,
                                    study_field_name=study_array_field_name,
                                    is_dictionary_term=config_item.is_dictionary_term,
                                )
                                ct_term_root_nodes.append(ct_term_root_node)
                    if study_array_field_value:
                        # If the value is set, create a StudyTextField node and (optionally) link it to matching CT term.
                        study_array_field_node = (
                            StudyArrayField.get_specific_field_currently_used_in_study(
                                study_uid=study_root.uid,
                                field_name=study_array_field_name,
                                value=study_array_field_value,
                            )
                        )
                        if study_array_field_node is None or to_delete:
                            study_array_field_node = StudyArrayField.create(
                                {
                                    "value": study_array_field_value,
                                    "field_name": study_array_field_name,
                                }
                            )[0]
                        for term_root_node in ct_term_root_nodes:
                            if not config_item.is_dictionary_term:
                                study_array_field_node.has_type.connect(term_root_node)
                            else:
                                study_array_field_node.has_dictionary_type.connect(
                                    term_root_node
                                )
                        if not to_delete:
                            expected_latest_value.has_array_field.connect(
                                study_array_field_node
                            )
                    elif (
                        not study_array_field_value
                        and study_array_field_null_value_code is not None
                    ):
                        study_array_field_node = (
                            StudyArrayField.get_specific_field_currently_used_in_study(
                                study_uid=study_root.uid,
                                field_name=study_array_field_name,
                                value=study_array_field_value,
                                null_value_code=study_array_field_null_value_code,
                            )
                        )
                        if study_array_field_node is None or to_delete:
                            study_array_field_node = StudyArrayField.create(
                                {"value": [], "field_name": study_array_field_name}
                            )[0]
                        for ct_term_root_node in ct_term_root_nodes:
                            study_array_field_node.has_type.connect(ct_term_root_node)
                        null_value_reason_node = self._get_associated_ct_term_root_node(
                            term_uid=study_array_field_null_value_code,
                            study_field_name="Null Flavor",
                        )
                        study_array_field_node.has_reason_for_null_value.connect(
                            null_value_reason_node
                        )
                        if not to_delete:
                            expected_latest_value.has_array_field.connect(
                                study_array_field_node
                            )

                if (
                    prev_study_array_field_node is not None
                    and (prev_study_array_field_node != study_array_field_node)
                    and previous_value is expected_latest_value
                ):
                    expected_latest_value.has_array_field.disconnect(
                        prev_study_array_field_node
                    )
                if study_array_field_node != prev_study_array_field_node:
                    self._generate_study_field_audit_node(
                        study_root_node=study_root,
                        study_field_node_after=study_array_field_node,
                        study_field_node_before=prev_study_array_field_node,
                        change_status=None,
                        author_id=self.audit_info.author_id,
                        date=date,
                        to_delete=to_delete,
                    )

    def _maintain_study_registry_id_fields_relationships(
        self,
        study_root: StudyRoot,
        previous_snapshot: StudyDefinitionSnapshot,
        current_snapshot: StudyDefinitionSnapshot,
        previous_value: StudyValue,
        expected_latest_value: StudyValue,
        date: datetime,
    ):
        curr_metadata = current_snapshot.current_metadata
        prev_metadata = previous_snapshot.current_metadata
        for config_item in [
            item
            for item in FieldConfiguration.default_field_config()
            if item.study_field_data_type == StudyFieldType.REGISTRY
        ]:
            study_registry_id_value = getattr(
                curr_metadata, config_item.study_field_name
            )  # current field value
            prev_study_registry_id_value = getattr(
                prev_metadata, config_item.study_field_name
            )  # previous field value
            study_registry_id_name = config_item.study_field_name_api  # field name

            if config_item.study_field_null_value_code is not None:
                study_registry_null_value_code = getattr(
                    curr_metadata, config_item.study_field_null_value_code
                )
                prev_study_registry_null_value_code = getattr(
                    prev_metadata, config_item.study_field_null_value_code
                )
            else:
                prev_study_registry_null_value_code = None
                study_registry_null_value_code = None

            if (
                study_registry_id_value != prev_study_registry_id_value
                or previous_value is not expected_latest_value
                or prev_study_registry_null_value_code != study_registry_null_value_code
            ):
                study_registry_id_text_field_node = None
                null_value_code = (
                    None
                    if prev_study_registry_id_value
                    else prev_study_registry_null_value_code
                )
                prev_study_registry_id_text_field_node = (
                    StudyTextField.get_specific_field_currently_used_in_study(
                        study_uid=study_root.uid,
                        field_name=study_registry_id_name,
                        value=prev_study_registry_id_value,
                        null_value_code=null_value_code,
                    )
                )
                # check if the study field needs to be deleted
                to_delete = False
                if (
                    study_registry_id_value is None
                    and study_registry_null_value_code is None
                ):
                    if (
                        study_registry_id_value is None
                        and prev_study_registry_id_value is not None
                    ):
                        study_registry_id_value = prev_study_registry_id_value
                        to_delete = True
                    elif (
                        study_registry_null_value_code is None
                        and prev_study_registry_null_value_code is not None
                    ):
                        study_registry_null_value_code = (
                            prev_study_registry_null_value_code
                        )
                        to_delete = True

                if study_registry_id_value is not None:
                    study_registry_id_text_field_node = (
                        self._get_or_create_study_field_node(
                            study_field=StudyTextField,
                            study_root=study_root,
                            study_field_name=study_registry_id_name,
                            study_field_value=study_registry_id_value,
                            term_root_node=None,
                            to_delete=to_delete,
                        )
                    )
                    if not to_delete:
                        expected_latest_value.has_text_field.connect(
                            study_registry_id_text_field_node
                        )

                elif study_registry_null_value_code is not None:
                    study_registry_id_text_field_node = (
                        self._get_or_create_study_field_node(
                            study_field=StudyTextField,
                            study_root=study_root,
                            study_field_name=study_registry_id_name,
                            study_field_value=study_registry_id_value,
                            term_root_node=None,
                            null_value_code=study_registry_null_value_code,
                            to_delete=to_delete,
                        )
                    )
                    if not to_delete:
                        expected_latest_value.has_text_field.connect(
                            study_registry_id_text_field_node
                        )
                if (
                    prev_study_registry_id_text_field_node is not None
                    and (
                        prev_study_registry_id_text_field_node
                        != study_registry_id_text_field_node
                    )
                    and previous_value is expected_latest_value
                ):
                    expected_latest_value.has_text_field.disconnect(
                        prev_study_registry_id_text_field_node
                    )
                if (
                    study_registry_id_text_field_node
                    != prev_study_registry_id_text_field_node
                ):
                    self._generate_study_field_audit_node(
                        study_root_node=study_root,
                        study_field_node_after=study_registry_id_text_field_node,
                        study_field_node_before=prev_study_registry_id_text_field_node,
                        change_status=None,
                        author_id=self.audit_info.author_id,
                        date=date,
                        to_delete=to_delete,
                    )

    @classmethod
    def add_value_and_null_value_code_to_dict(
        cls,
        study_field_node_value,
        study_field_node_name,
        null_value_code,
        retrieved_data,
    ):
        null_value_code_suffix = "_null_value_code"
        null_value_field_name = (
            cls.truncate_code_or_codes_suffix(study_field_node_name)
            + null_value_code_suffix
        )
        retrieved_data[study_field_node_name] = study_field_node_value
        if null_value_code is not None:
            retrieved_data[null_value_field_name] = null_value_code.uid
        else:
            retrieved_data[null_value_field_name] = None

    @classmethod
    def _get_text_field_value(cls, text_field_node) -> str:
        if type_node := text_field_node.has_type.get_or_none():
            return type_node.uid
        return text_field_node.value

    @classmethod
    def _get_array_field_values(cls, array_field_node) -> list[str]:
        if type_nodes := array_field_node.has_type.all():
            return sorted(node.uid for node in type_nodes)
        return array_field_node.value

    @classmethod
    def _retrieve_data_from_study_value(cls, study_value: StudyValue) -> dict[Any, Any]:
        """
        Function traverses relationships from StudyValue to different StudyFields and retrieves the data from
        StudyField nodes to populate that data to the StudyDefinitionSnapshot.
        Returns data in dictionary that maps StudyField field_names into StudyField values.
        :param study_value:
        :return dict:
        """

        study_project_node = study_value.has_project.get_or_none()
        project_node = study_project_node.has_field.get_or_none()

        study_text_field_nodes = study_value.has_text_field.all()
        null_value_reason_text_fields = [
            study_text_field_node.has_reason_for_null_value.get_or_none()
            for study_text_field_node in study_text_field_nodes
        ]

        study_int_field_nodes = study_value.has_int_field.all()
        null_value_reason_int_fields = [
            study_int_field_node.has_reason_for_null_value.get_or_none()
            for study_int_field_node in study_int_field_nodes
        ]

        study_array_field_nodes = study_value.has_array_field.all()
        null_value_reason_array_fields = [
            study_array_field_node.has_reason_for_null_value.get_or_none()
            for study_array_field_node in study_array_field_nodes
        ]

        study_boolean_field_nodes = study_value.has_boolean_field.all()
        null_value_reason_boolean_fields = [
            study_boolean_field_node.has_reason_for_null_value.get_or_none()
            for study_boolean_field_node in study_boolean_field_nodes
        ]

        study_time_field_nodes = study_value.has_time_field.all()
        null_value_reason_duration_fields = [
            study_time_field_node.has_reason_for_null_value.get_or_none()
            for study_time_field_node in study_time_field_nodes
        ]

        retrieved_data = {}
        retrieved_data["project_number"] = (
            project_node.project_number if project_node else None
        )

        for study_text_field_node, null_value_reason_text_field in zip(
            study_text_field_nodes, null_value_reason_text_fields
        ):
            cls.add_value_and_null_value_code_to_dict(
                cls._get_text_field_value(study_text_field_node),
                study_text_field_node.field_name,
                null_value_reason_text_field,
                retrieved_data,
            )

        for study_int_field_node, null_value_reason_int_field in zip(
            study_int_field_nodes, null_value_reason_int_fields
        ):
            cls.add_value_and_null_value_code_to_dict(
                study_int_field_node.value,
                study_int_field_node.field_name,
                null_value_reason_int_field,
                retrieved_data,
            )

        for study_array_field_node, null_value_reason_array_field in zip(
            study_array_field_nodes, null_value_reason_array_fields
        ):
            cls.add_value_and_null_value_code_to_dict(
                cls._get_array_field_values(study_array_field_node),
                study_array_field_node.field_name,
                null_value_reason_array_field,
                retrieved_data,
            )

        for study_boolean_field_node, null_value_reason_boolean_field in zip(
            study_boolean_field_nodes, null_value_reason_boolean_fields
        ):
            cls.add_value_and_null_value_code_to_dict(
                study_boolean_field_node.value,
                study_boolean_field_node.field_name,
                null_value_reason_boolean_field,
                retrieved_data,
            )

        for study_time_field_node, null_value_reason_duration_field in zip(
            study_time_field_nodes, null_value_reason_duration_fields
        ):
            cls.add_value_and_null_value_code_to_dict(
                study_time_field_node.value,
                study_time_field_node.field_name,
                null_value_reason_duration_field,
                retrieved_data,
            )
        return retrieved_data

    @classmethod
    def _assign_snapshot_ver_properties_from_ver_relationship(
        cls,
        snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot,
        ver_relationship: VersionRelationship,
    ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot:
        snapshot.version_timestamp = ver_relationship.start_date
        snapshot.version_author = UserInfoService.get_author_username_from_id(
            ver_relationship.author_id
        )
        snapshot.version_description = ver_relationship.change_description
        snapshot.version_number = (
            Decimal(ver_relationship.version) if ver_relationship.version else None
        )
        return snapshot

    @classmethod
    def _study_metadata_snapshot_from_study_value(
        cls, study_value: StudyValue
    ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot:
        retrieved_data = cls._retrieve_data_from_study_value(study_value)

        snapshot_dict: dict[Any, Any] = {}
        for config_item in FieldConfiguration.default_field_config():
            if config_item.study_field_grouping == "ver_metadata":
                snapshot_dict[config_item.study_field_name] = None
            elif hasattr(study_value, config_item.study_field_name):
                snapshot_dict[config_item.study_field_name] = getattr(
                    study_value, config_item.study_field_name
                )
            elif (
                config_item.study_field_data_type == StudyFieldType.CODELIST_MULTISELECT
            ):
                snapshot_dict[config_item.study_field_name] = retrieved_data.get(
                    config_item.study_field_name_api, []
                )
            else:
                snapshot_dict[config_item.study_field_name] = retrieved_data.get(
                    config_item.study_field_name_api
                )
        return StudyDefinitionSnapshot.StudyMetadataSnapshot(**snapshot_dict)

    @overload
    @classmethod
    def _study_metadata_snapshot_from_cypher_res(
        cls, metadata_section: dict[Any, Any]
    ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot: ...
    @overload
    @classmethod
    def _study_metadata_snapshot_from_cypher_res(
        cls, metadata_section: None
    ) -> None: ...
    @classmethod
    def _study_metadata_snapshot_from_cypher_res(
        cls, metadata_section: dict[Any, Any] | None
    ) -> StudyDefinitionSnapshot.StudyMetadataSnapshot | None:
        """
        Function maps the part of the result of the cypher query that holds Study metadata information
        into StudyMetadataSnapshot that is a part of StudyDefinitionSnapshot.
        :param metadata_section:
        :return StudyDefinitionSnapshot.StudyMetadataSnapshot | None:
        """
        if metadata_section is None:
            return None
        snapshot_dict = {
            "study_number": metadata_section["study_number"],
            "subpart_id": metadata_section["subpart_id"],
            "study_acronym": metadata_section["study_acronym"],
            "study_subpart_acronym": metadata_section["study_subpart_acronym"],
            "study_id_prefix": metadata_section["study_id_prefix"],
            "project_number": metadata_section["project_number"],
            "description": metadata_section["description"],
            "version_timestamp": convert_to_datetime(
                value=metadata_section["version_timestamp"]
            ),
            "version_author": UserInfoService.get_author_username_from_id(
                metadata_section["version_author_id"]
            ),
            "version_description": metadata_section.get("version_description"),
            "version_number": metadata_section.get("version_number"),
            "study_title": metadata_section["study_title"],
            "study_short_title": metadata_section["study_short_title"],
        }
        for config_item in FieldConfiguration.default_field_config():
            if config_item.study_field_name not in snapshot_dict:
                if (
                    config_item.study_field_data_type
                    == StudyFieldType.CODELIST_MULTISELECT
                ):
                    snapshot_dict[config_item.study_field_name] = []
                else:
                    snapshot_dict[config_item.study_field_name] = None
        return StudyDefinitionSnapshot.StudyMetadataSnapshot(**snapshot_dict)

    @classmethod
    def _study_value_from_study_metadata_snapshot(
        cls, metadata_snapshot: StudyDefinitionSnapshot.StudyMetadataSnapshot
    ) -> StudyValue:
        # we should keep keep (ready made) study_id in DB for ease of sorting and selection
        _study_id = (
            None
            if (
                metadata_snapshot.study_number is None
                or metadata_snapshot.study_id_prefix is None
            )
            else f"{metadata_snapshot.study_id_prefix}-{metadata_snapshot.study_number}"
        )

        value = StudyValue(
            study_id=_study_id,
            study_number=metadata_snapshot.study_number,
            subpart_id=metadata_snapshot.subpart_id,
            study_acronym=metadata_snapshot.study_acronym,
            study_subpart_acronym=metadata_snapshot.study_subpart_acronym,
            description=metadata_snapshot.description,
            study_id_prefix=metadata_snapshot.study_id_prefix,
        )

        return value

    def _create(self, snapshot: StudyDefinitionSnapshot) -> None:
        self._ensure_transaction()
        if (
            snapshot.released_metadata is not None
            or len(snapshot.locked_metadata_versions) > 0
        ):
            # The use case of creating a new object having anything more than draft metadata
            # is not supported (currently it's irrelevant).
            raise NotImplementedError(
                "The case of creating a new object having anything more"
                " than draft metadata is not supported (yet?)."
            )

        # Create root & value nodes based on the specified NeoModel class.
        root = StudyRoot(uid=snapshot.uid)
        assert snapshot.current_metadata is not None
        value = self._study_value_from_study_metadata_snapshot(
            snapshot.current_metadata
        )
        root.save()
        value.save()
        rel_properties = self._create_versioning_data(snapshot)
        self._db_create_relationship(root.latest_value, value, rel_properties)
        self._db_create_relationship(root.latest_draft, value, rel_properties)
        self._db_create_relationship(root.has_version, value, rel_properties)
        project_node = Project.nodes.get(
            project_number=snapshot.current_metadata.project_number
        )
        study_project_field_node = StudyProjectField()
        study_project_field_node.save()
        study_project_field_node.has_field.connect(project_node)
        value.has_project.connect(study_project_field_node)

        # Log the study value creation in the audit trail
        date = datetime.now(timezone.utc)
        self._generate_study_value_audit_node(
            study_root_node=root,
            study_value_node_after=value,
            study_value_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=date,
        )
        # Log the link to the project in the audit trail
        self._generate_study_field_audit_node(
            study_root_node=root,
            study_field_node_after=study_project_field_node,
            study_field_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=date,
        )

    @staticmethod
    def _generate_study_value_audit_node(
        study_root_node: StudyRoot,
        study_value_node_after: StudyField | None,
        study_value_node_before: StudyField | None,
        change_status: str | None,
        author_id: str | None,
        date: datetime,
    ) -> StudyAction:
        if study_value_node_before is None:
            audit_node = Create()
        elif study_value_node_after is None:
            audit_node = Delete()
        else:
            audit_node = Edit()
        audit_node.status = change_status
        audit_node.author_id = author_id
        audit_node.date = date
        audit_node.save()

        if study_value_node_before:
            audit_node.study_value_has_before.connect(study_value_node_before)
        if study_value_node_after:
            audit_node.study_value_node_has_after.connect(study_value_node_after)

        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def _create_versioning_data(
        self, snapshot: StudyDefinitionSnapshot
    ) -> Mapping[str, Any]:
        assert snapshot.current_metadata is not None
        assert snapshot.current_metadata.version_author is None or (
            self.audit_info.author_id
            and snapshot.current_metadata.version_author
            == UserInfoService.get_author_username_from_id(self.audit_info.author_id)
        )
        data = {
            "start_date": snapshot.current_metadata.version_timestamp,
            "end_date": None,
            "status": snapshot.study_status,
            "version": (
                len(snapshot.locked_metadata_versions)
                if snapshot.study_status == StudyStatus.LOCKED.value
                else None
            ),
            "change_description": snapshot.current_metadata.version_description,
            "author_id": self.audit_info.author_id,
        }
        return data

    def _retrieve_fields_audit_trail(
        self, uid: str
    ) -> list[StudyFieldAuditTrailEntryAR] | None:
        query = """
        MATCH (root:StudyRoot {uid: $studyuid})-[:AUDIT_TRAIL]->(action)

        OPTIONAL MATCH (action)-[:BEFORE]->(before)
        WHERE "StudyField" in labels(before) or "StudyValue" in labels(before)
        OPTIONAL MATCH (action)-[:AFTER]->(after)
        WHERE "StudyField" in labels(after) or "StudyValue" in labels(after)
        
        // Preprocess the audit trail structure into the format expected by the API.
        WITH root.uid as study_uid, 
            [x in labels(action) WHERE x <> "StudyAction"][0] as action, 
            action.date as date,
            action.author_id AS author_id,
            CASE
                WHEN before is NULL THEN NULL
                WHEN (before:StudyValue) THEN ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]
                WHEN (before:StudyProjectField) THEN ["project_number"]
                WHEN (before:StudyField) THEN [before.field_name]
                ELSE ["Unknown"]
            END as before_field, 
            CASE
                WHEN before is NULL THEN [NULL,NULL,NULL,NULL]
                WHEN (before:StudyValue) THEN [before.study_acronym, before.study_subpart_acronym, before.study_id_prefix,
                before.study_number, before.description]
                WHEN (before:StudyProjectField) THEN [head([(before)<-[:HAS_FIELD]-(p) | p.project_number])]
                WHEN (before:StudyArrayField) THEN [apoc.text.join(before.value, ', ')]
                WHEN (NOT before.field_name in ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]) THEN [before.value]
            END as before_value, 
            CASE
                //WHEN ("Delete" in labels(action) AND "StudyField" in labels(after)) OR (after is NULL) THEN [NULL,NULL,NULL,NULL]
                WHEN (after:StudyValue) THEN ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]
                WHEN (after:StudyProjectField) THEN ["project_number"]
                WHEN (after:StudyField) THEN [after.field_name]
                ELSE ["Unknown"]
            END as after_field, 
            CASE
                //WHEN ("Delete" in labels(action) AND "StudyField" in labels(after)) OR (after is NULL) THEN [NULL]
                WHEN (after:StudyValue) THEN [after.study_acronym, after.study_subpart_acronym, after.study_id_prefix, after.study_number, after.description]
                WHEN (after:StudyProjectField) THEN [head([(after)<-[:HAS_FIELD]-(p) | p.project_number])]
                WHEN (after:StudyArrayField) THEN [apoc.text.join(after.value, ', ')]
                WHEN (NOT after.field_name in ["study_acronym", "study_subpart_acronym", "study_id", "study_number"]) THEN [after.value]
            END as after_value
        WITH study_uid, date, author_id, action, coalesce(before_field,after_field) as field, before_value as before, after_value as after 
        ORDER BY field ASC
        WITH study_uid, 
            date, 
            author_id, 
            action, 
            apoc.coll.zip(field, apoc.coll.zip(before,after)) as field_with_values_array
            CALL {
                WITH author_id
                OPTIONAL MATCH (author: User)
                WHERE author.user_id = author_id
                RETURN coalesce(author.username, author_id) AS author_username 
            }
        UNWIND field_with_values_array as field_with_value
        WITH *
        WHERE NOT (field_with_value[1][0] IS NOT NULL 
                    AND field_with_value[1][1] IS NOT NULL 
                    AND (field_with_value[1][0] = field_with_value[1][1] and not action = 'Delete')
                )
            AND NOT (field_with_value[1][0] IS NULL 
                    AND field_with_value[1][1] IS NULL
                )
        RETURN study_uid, toString(date) as date, author_id, collect(
            distinct  {action:action, 
             field:field_with_value[0], 
             before:toString(field_with_value[1][0]),  
             after:toString(field_with_value[1][1])
             }) as actions,
             author_username

        ORDER BY date DESC

      """

        query_parameters = {"studyuid": uid}
        result_array, _ = db.cypher_query(query, query_parameters)

        # if the study is not found, return None.
        if len(result_array) == 0:
            return None
        audit_trail = [
            StudyFieldAuditTrailEntryAR(
                study_uid=row[0],
                author_id=row[2],
                author_username=row[4],
                date=row[1],
                actions=[
                    StudyFieldAuditTrailActionVO(
                        section=self.get_section_name_for_study_field(action["field"]),
                        action=action["action"],
                        field_name=self.truncate_code_or_codes_suffix(action["field"]),
                        before_value=action["before"],
                        after_value=action["after"],
                    )
                    for action in row[3]
                    if action["field"] not in ["study_id_prefix"]
                ],
            )
            for row in result_array
        ]
        return audit_trail

    @classmethod
    def truncate_code_or_codes_suffix(
        cls,
        field_name: str,
    ) -> str:
        """
        Truncates code or codes name suffix if exists
        """
        suffixes_to_truncate = ["_code", "_codes"]
        for suffix in suffixes_to_truncate:
            if field_name.endswith(suffix) and "null_value_code" not in field_name:
                field_name = field_name[: -(len(suffix))]
                if field_name == "trial_intent_types":
                    field_name = "trial_intent_type"
        return field_name

    @classmethod
    def get_section_name_for_study_field(cls, field):
        """
        For a given field name, find what logical section of the study properties it belongs to.
        """
        if (
            field in [field.name for field in fields(StudyIdentificationMetadataVO)]  # type: ignore[arg-type]
            or field == "study_id"
        ):
            return "identification_metadata"
        if field in [field.name for field in fields(RegistryIdentifiersVO)]:
            return "registry_identifiers"
        if field in [field.name for field in fields(StudyVersionMetadataVO)]:  # type: ignore[arg-type]
            return "version_metadata"
        if field in [field.name for field in fields(HighLevelStudyDesignVO)]:
            return "high_level_study_design"
        if field in [field.name for field in fields(StudyPopulationVO)]:
            return "study_population"
        if field in [field.name for field in fields(StudyInterventionVO)]:
            return "study_intervention"
        if field in [field.name for field in fields(StudyDescriptionVO)]:
            return "study_description"
        # A study field was found in the audit trail that does not belong to any sections:
        return "Unknown"

    def _build_snapshot_match_clause(
        self,
        study_selection_object_node_id,
        study_selection_object_node_type,
        filter_query_parameters: dict[Any, Any],
        deleted: bool,
    ) -> str:
        if study_selection_object_node_id:
            match_clause = f"""
MATCH (:{study_selection_object_node_type.ROOT_NODE_LABEL}{{uid:$sson_id}})-->(:{study_selection_object_node_type.VALUE_NODE_LABEL})
<-[:{study_selection_object_node_type.STUDY_SELECTION_REL_LABEL}]-(:StudySelection)<-[:{study_selection_object_node_type.STUDY_VALUE_REL_LABEL}]-(sv:StudyValue)
WITH sv
MATCH (sr:StudyRoot)-[:LATEST]->(sv)
"""
            filter_query_parameters["sson_id"] = study_selection_object_node_id
        else:
            match_clause = "MATCH (sr:StudyRoot)-[:LATEST]->(sv:StudyValue)"
        match_clause += (
            f"WHERE {'' if deleted else 'NOT'} EXISTS((sv)<-[:BEFORE]-(:Delete))"
        )
        return match_clause

    def _build_snapshot_alias_clause(self) -> str:
        alias_clause = """
                    sr, sv,
                    head([(sr)-[ll:LATEST_LOCKED]->() | ll]) AS llr,
                    head([(sr)-[lr:LATEST_RELEASED]->(lrn) | {lrr:lr, svr: lrn}]) AS released,
                    head([(sr)-[ld:LATEST_DRAFT]->(sdr) | {ldr:ld, sdr: sdr}]) AS draft,
                    head([(sr)-[hv:HAS_VERSION {status: 'LOCKED'}]->(hvn) | {has_version:hv, svlh:hvn}]) AS locked,
                    head([(sv)<-[:HAS_STUDY_SUBPART]-(:StudyValue)<-[:LATEST]-(parent:StudyRoot) | parent.uid]) AS study_parent_part_uid,
                    [(sv)-[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:LATEST]-(sub:StudyRoot)
                     | sub.uid] AS study_subpart_uids,
                    exists((sr)-[:LATEST_LOCKED]->()) AS has_latest_locked,
                    exists((sr)-[:LATEST_DRAFT]->()) AS has_latest_draft,
                    exists((sr)-[:LATEST_RELEASED]->()) AS has_latest_released,
                    exists((sv)-[:HAS_STUDY_FOOTNOTE]->()) AS has_study_footnote,
                    exists((sv)-[:HAS_STUDY_OBJECTIVE]->()) AS has_study_objective,
                    exists((sv)-[:HAS_STUDY_ENDPOINT]->()) AS has_study_endpoint,
                    exists((sv)-[:HAS_STUDY_CRITERIA]->()) AS has_study_criteria,
                    exists((sv)-[:HAS_STUDY_ACTIVITY]->()) AS has_study_activity,
                    exists((sv)-[:HAS_STUDY_ACTIVITY_INSTRUCTION]->()) AS has_study_activity_instruction
                    WITH sr,
                    sv,
                    study_parent_part_uid,
                    study_subpart_uids,
                    llr,
                    released,
                    draft,
                    locked,
                    has_latest_locked,
                    has_latest_draft,
                    has_latest_released,
                    has_study_footnote,
                    has_study_objective,
                    has_study_endpoint,
                    has_study_criteria,
                    has_study_activity,
                    has_study_activity_instruction,
                    locked.svlh AS svlh,
                    locked.has_version AS has_version,
                    released.lrr AS lrr,
                    released.svr AS svr,
                    draft.ldr AS ldr,
                    draft.sdr AS sdr
                    ORDER BY has_version.end_date ASC
                    WITH *,
                        sr.uid as uid,
                        CASE WHEN ldr.end_date IS NULL THEN 'DRAFT' ELSE 'LOCKED' END as study_status,
                        {
                            study_id: sv.study_id,
                            study_number: sv.study_number,
                            subpart_id: sv.subpart_id,
                            study_acronym: sv.study_acronym,
                            study_subpart_acronym: sv.study_subpart_acronym,
                            study_id_prefix: sv.study_id_prefix,
                            description: sv.description,
                            project_number: head([(sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sv)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sv)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: CASE WHEN ldr.end_date IS NULL THEN ldr.start_date ELSE llr.start_date END,
                            version_number: CASE WHEN ldr.end_date IS NULL THEN ldr.version ELSE llr.version END,
                            version_author_id: CASE WHEN ldr.end_date IS NULL THEN ldr.author_id ELSE llr.author_id END
                        } AS current_metadata,
                        CASE WHEN has_latest_locked THEN
                        {
                            locked_metadata_array: [
                                locked_version IN collect({
                                    study_id: svlh.study_id,
                                    study_number: svlh.study_number,
                                    subpart_id: svlh.subpart_id,
                                    study_acronym: svlh.study_acronym,
                                    study_subpart_acronym: svlh.study_subpart_acronym,
                                    study_id_prefix: svlh.study_id_prefix,
                                    description: svlh.description,
                                    project_number: head([(svlh)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                                    study_title: head([(svlh)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                                    study_short_title: head([(svlh)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                                    version_timestamp: has_version.start_date,
                                    version_number: has_version.version,
                                    version_author_id: has_version.author_id
                                })
                            ]
                        }  END AS locked_metadata_versions,
                        CASE WHEN has_latest_released AND lrr.end_date IS NULL THEN
                        {
                            study_id: svr.study_id,
                            study_number: svr.study_number,
                            subpart_id: svr.subpart_id,
                            study_acronym: svr.study_acronym,
                            study_subpart_acronym: svr.study_subpart_acronym,
                            study_id_prefix: svr.study_id_prefix,
                            description: svr.description,
                            project_number: head([(svr)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(svr)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(svr)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: lrr.start_date,
                            version_number: lrr.version_number,
                            version_author_id: lrr.author_id
                        }  END AS released_metadata,
                        CASE WHEN has_latest_draft THEN
                        {
                            study_id: sdr.study_id,
                            study_number: sdr.study_number,
                            subpart_id: sdr.subpart_id,
                            study_acronym: sdr.study_acronym,
                            study_subpart_acronym: sdr.study_subpart_acronym,
                            study_id_prefix: sdr.study_id_prefix,
                            description: sdr.description,
                            project_number: head([(sdr)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sdr)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sdr)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: ldr.start_date,
                            version_number: ldr.version_number,
                            version_author_id: ldr.author_id
                        }  END AS draft_metadata,
                        has_study_footnote,
                        has_study_objective,
                        has_study_endpoint,
                        has_study_criteria,
                        has_study_activity,
                        has_study_activity_instruction
                    """
        return alias_clause

    def _update_snapshot_filter_by(
        self,
        filter_by: dict[str, dict[str, Any]],
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
    ) -> dict[str, dict[str, Any]]:
        if has_study_footnote is not None:
            filter_by["has_study_footnote"] = {"v": [has_study_footnote]}
        if has_study_objective is not None:
            filter_by["has_study_objective"] = {"v": [has_study_objective]}
        if has_study_endpoint is not None:
            filter_by["has_study_endpoint"] = {"v": [has_study_endpoint]}
        if has_study_criteria is not None:
            filter_by["has_study_criteria"] = {"v": [has_study_criteria]}
        if has_study_activity is not None:
            filter_by["has_study_activity"] = {"v": [has_study_activity]}
        if has_study_activity_instruction is not None:
            filter_by["has_study_activity_instruction"] = {
                "v": [has_study_activity_instruction]
            }
        return filter_by

    def _retrieve_all_snapshots(
        self,
        has_study_footnote: bool | None = None,
        has_study_objective: bool | None = None,
        has_study_endpoint: bool | None = None,
        has_study_criteria: bool | None = None,
        has_study_activity: bool | None = None,
        has_study_activity_instruction: bool | None = None,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
        study_selection_object_node_id: int | str | None = None,
        study_selection_object_node_type: NodeMeta | None = None,
        deleted: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        # To build StudyDefinitionSnapshot (domain object) we need 5 main members:
        # * uid
        # * study_status
        # * current_metadata (can't be None)
        #   - retrieved in 'AS current_metadata' section
        # * released_metadata (can be None)
        #   - retrieved in 'AS released_metadata" section (if there is such need)
        # * locked_metadata_versions (can be None) - array of locked_metadata ordered by end_date property
        #   - retrieved in 'AS locked_metadata_versions' section (if there is such need)
        # All of the above members are fetched in the query below.
        # The following query contains some representation logic (mainly in parts where the CASE clause is used)
        # The logic was taken from the already existing implementation of retrieving single Study.

        if sort_by is None:
            sort_by = {"uid": True}

        if filter_by is None:
            filter_by = {}

        # Specific filtering
        filter_query_parameters: dict[Any, Any] = {}

        match_clause = self._build_snapshot_match_clause(
            study_selection_object_node_id,
            study_selection_object_node_type,
            filter_query_parameters,
            deleted,
        )
        alias_clause = self._build_snapshot_alias_clause()
        filter_by = self._update_snapshot_filter_by(
            filter_by,
            has_study_footnote,
            has_study_objective,
            has_study_endpoint,
            has_study_criteria,
            has_study_activity,
            has_study_activity_instruction,
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
            return_model=StudyDefinitionSnapshot,
        )

        query.parameters.update(filter_query_parameters)
        result_array, attributes_names = query.execute()

        # the following code formats the output of the neomodel query
        # it assigns the names for the properties of each Study, as neomodel
        # returns names of the properties in the separate array
        studies = []
        for study in result_array:
            study_dictionary = {}
            for study_property, attribute_name in zip(study, attributes_names):
                study_dictionary[attribute_name] = study_property
            studies.append(study_dictionary)

        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]
            else:
                total = 0
        else:
            total = 0

        return GenericFilteringReturn(
            items=self._retrieve_all_snapshots_from_cypher_query_result(
                studies, deleted=deleted
            ),
            total=total,
        )

    def _retrieve_study_snapshot_history(
        self,
        study_uid: str,
        sort_by: dict[str, bool] | None = None,
        page_number: int = 1,
        page_size: int = 0,
        filter_by: dict[str, dict[str, Any]] | None = None,
        filter_operator: FilterOperator = FilterOperator.AND,
        total_count: bool = False,
    ) -> GenericFilteringReturn[StudyDefinitionSnapshot]:
        exceptions.ValidationException.raise_if(
            self.check_if_study_is_deleted(study_uid=study_uid),
            msg=f"Study with UID '{study_uid}' is deleted.",
        )

        # Specific filtering
        filter_query_parameters = {"study_uid": study_uid}

        match_clause = """MATCH (sr:StudyRoot {uid: $study_uid})-[has_version:HAS_VERSION]->(sv:StudyValue)
        WITH *,
        head([(sr)-[latest_draft:LATEST_DRAFT]->(sv) | latest_draft]) AS latest_draft
        WHERE NOT EXISTS((sv)<-[:BEFORE]-(:Delete)) AND 
        (has_version.status <> 'DRAFT' OR (latest_draft IS NOT NULL AND latest_draft.end_date IS NULL))"""
        # Aliases clause
        alias_clause = """
                    sr, sv, has_version,
                    head([(sv)<-[:HAS_STUDY_SUBPART]-(:StudyValue)<-[:LATEST]-(parent:StudyRoot) | parent.uid]) AS study_parent_part_uid,
                    [(sv)-[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:LATEST]-(sub:StudyRoot)
                     | sub.uid] AS study_subpart_uids
                    ORDER BY has_version.start_date DESC, has_version.status
                    WITH
                        sr.uid as uid,
                        study_parent_part_uid,
                        study_subpart_uids,
                        has_version.status as study_status,
                        {
                            study_id: sv.study_id,
                            study_number: sv.study_number,
                            subpart_id: sv.subpart_id,
                            study_acronym: sv.study_acronym,
                            study_subpart_acronym: sv.study_subpart_acronym,
                            study_id_prefix: sv.study_id_prefix,
                            description: sv.description,
                            project_number: head([(sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sv)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sv)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: has_version.start_date,
                            version_author_id: has_version.author_id,
                            version_description: has_version.change_description,
                            version_number: has_version.version
                            
                        } AS current_metadata,
                        CASE WHEN has_version.status="LOCKED" THEN
                        {
                            locked_metadata_array: [
                                locked_version IN collect({
                                    study_id: sv.study_id,
                                    study_number: sv.study_number,
                                    subpart_id: sv.subpart_id,
                                    study_acronym: sv.study_acronym,
                                    study_subpart_acronym: sv.study_subpart_acronym,
                                    study_id_prefix: sv.study_id_prefix,
                                    description: sv.description,
                                    project_number: head([(sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                                    study_title: head([(sv)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                                    study_short_title: head([(sv)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                                    version_timestamp: has_version.start_date,
                                    version_author_id: has_version.author_id,
                                    version_description: has_version.change_description,
                                    version_number: has_version.version
                                })
                            ]
                        }  END AS locked_metadata_versions,
                        CASE WHEN has_version.status="RELEASED" THEN
                        {
                            study_id: sv.study_id,
                            study_number: sv.study_number,
                            subpart_id: sv.subpart_id,
                            study_acronym: sv.study_acronym,
                            study_subpart_acronym: sv.study_subpart_acronym,
                            study_id_prefix: sv.study_id_prefix,
                            description: sv.description,
                            project_number: head([(sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sv)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sv)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: has_version.start_date,
                            version_author_id: has_version.author_id,
                            version_description: has_version.change_description,
                            version_number: has_version.version
                        }  END AS released_metadata,
                        CASE WHEN has_version.status="DRAFT" THEN
                        {
                            study_id: sv.study_id,
                            study_number: sv.study_number,
                            subpart_id: sv.subpart_id,
                            study_acronym: sv.study_acronym,
                            study_subpart_acronym: sv.study_subpart_acronym,
                            study_id_prefix: sv.study_id_prefix,
                            description: sv.description,
                            project_number: head([(sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(p:Project) | p.project_number]),
                            study_title: head([(sv)-[:HAS_TEXT_FIELD]->(t:StudyTextField) WHERE t.field_name = "study_title" | t.value]),
                            study_short_title: head([(sv)-[:HAS_TEXT_FIELD]->(st:StudyTextField) WHERE st.field_name = "study_short_title" | st.value]),
                            version_timestamp: has_version.start_date,
                            version_author_id: has_version.author_id,
                            version_description: has_version.change_description,
                            version_number: has_version.version
                        }  END AS draft_metadata
                    """

        query = CypherQueryBuilder(
            match_clause=match_clause,
            alias_clause=alias_clause,
            sort_by=sort_by,
            page_number=page_number,
            page_size=page_size,
            filter_by=FilterDict.model_validate({"elements": filter_by}),
            filter_operator=filter_operator,
            total_count=total_count,
            return_model=StudyDefinitionSnapshot,
        )

        query.parameters.update(filter_query_parameters)

        result_array, attributes_names = query.execute()
        # the following code formats the output of the neomodel query
        # it assigns the names for the properties of each Study, as neomodel
        # returns names of the properties in the separate array
        studies = []
        for study in result_array:
            study_dictionary = {}
            for study_property, attribute_name in zip(study, attributes_names):
                study_dictionary[attribute_name] = study_property
            studies.append(study_dictionary)
        if total_count:
            count_result, _ = db.cypher_query(
                query=query.count_query, params=query.parameters
            )
            if len(count_result) > 0:
                total = count_result[0][0]
            else:
                total = 0
        else:
            total = 0

        return GenericFilteringReturn(
            items=self._retrieve_all_snapshots_from_cypher_query_result(studies),
            total=total,
        )

    def generate_uid(self) -> str:
        return StudyRoot.get_next_free_uid_and_increment_counter()

    @staticmethod
    def _generate_study_field_audit_node(
        study_root_node: StudyRoot,
        study_field_node_after: StudyField | None,
        study_field_node_before: StudyField | None,
        change_status: str | None,
        author_id: str | None,
        date: datetime,
        to_delete: bool = False,
    ) -> StudyAction:
        """
        Updates the audit trail when study fields are added, removed or modified.
        """
        if study_field_node_before is None:
            audit_node = Create()
        elif study_field_node_after is None or to_delete:
            audit_node = Delete()
        else:
            audit_node = Edit()
        audit_node.status = change_status
        audit_node.author_id = author_id
        audit_node.date = date
        audit_node.save()

        if study_field_node_before:
            audit_node.study_field_has_before.connect(study_field_node_before)
        if study_field_node_after:
            audit_node.study_field_node_has_after.connect(study_field_node_after)

        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    def get_preferred_time_unit(
        self,
        study_uid: str,
        for_protocol_soa: bool = False,
        study_value_version: str | None = None,
    ) -> NodeSet:
        filters = {
            "field_name": (
                settings.study_field_soa_preferred_time_unit_name
                if for_protocol_soa
                else settings.study_field_preferred_time_unit_name
            ),
        }
        if study_value_version:
            filters.update(
                {
                    "has_time_field__has_version__uid": study_uid,
                    "has_time_field__has_version|version": study_value_version,
                    "has_time_field__has_version|status": StudyStatus.RELEASED.value,
                }
            )
        else:
            filters.update(
                {
                    "has_time_field__latest_value__uid": study_uid,
                }
            )
        nodes = StudyTimeField.nodes.fetch_relations(
            "has_unit_definition__has_latest_value",
            "has_after__audit_trail",
        ).filter(**filters)
        return nodes.resolve_subgraph()

    def post_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> NodeSet:
        nodes = self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

        exceptions.AlreadyExistsException.raise_if(
            nodes,
            msg=f"There already exists a Preferred Time Unit for the Study with UID '{study_uid}'.",
        )

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()
        unit_definition = UnitDefinitionRoot.nodes.get(uid=unit_definition_uid)
        preferred_time_field_sf = StudyTimeField.create(
            {
                "value": unit_definition_uid,
                "field_name": (
                    settings.study_field_soa_preferred_time_unit_name
                    if for_protocol_soa
                    else settings.study_field_preferred_time_unit_name
                ),
            }
        )[0]
        preferred_time_field_sf.has_unit_definition.connect(unit_definition)
        latest_study_value.has_time_field.connect(preferred_time_field_sf)

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=preferred_time_field_sf,
            study_field_node_before=None,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )
        return self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

    def edit_preferred_time_unit(
        self, study_uid: str, unit_definition_uid: str, for_protocol_soa: bool = False
    ) -> NodeSet:
        # getting previous preferred time unit study field
        previous_time_field = self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

        exceptions.BusinessLogicException.raise_if(
            len(previous_time_field) > 1,
            msg="Returned more than one previous preferred StudyTimeField nodes",
        )
        exceptions.BusinessLogicException.raise_if(
            len(previous_time_field) == 0,
            msg="The previous preferred StudyTimeField node was not found",
        )

        previous_time_field = previous_time_field[0]

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()
        unit_definition = UnitDefinitionRoot.nodes.get(uid=unit_definition_uid)

        # creating (soa_)preferred_time_unit StudyTimeField node
        preferred_time_field_sf = StudyTimeField.create(
            {
                "value": unit_definition_uid,
                "field_name": (
                    settings.study_field_soa_preferred_time_unit_name
                    if for_protocol_soa
                    else settings.study_field_preferred_time_unit_name
                ),
            }
        )[0]

        # connecting (soa_)preferred_time_unit StudyTimeField node to the UnitDefinitionRoot node
        preferred_time_field_sf.has_unit_definition.connect(unit_definition)

        # connecting StudyValue node to the StudyTimeField node
        latest_study_value.has_time_field.connect(preferred_time_field_sf)

        # disconnecting StudyValue from the :BEFORE version of StudyTimeField
        latest_study_value.has_time_field.disconnect(previous_time_field)

        exceptions.BusinessLogicException.raise_if(
            previous_time_field.value == unit_definition_uid,
            msg=f"The Preferred Time Unit for the Study with UID '{study_uid}' is already '{unit_definition_uid}'.",
        )

        self._generate_study_field_audit_node(
            study_root_node=study_root,
            study_field_node_after=preferred_time_field_sf,
            study_field_node_before=previous_time_field,
            change_status=None,
            author_id=self.audit_info.author_id,
            date=datetime.now(timezone.utc),
        )
        return self.get_preferred_time_unit(
            study_uid=study_uid, for_protocol_soa=for_protocol_soa
        )

    def study_exists_by_uid(self, study_uid: str) -> bool:
        return bool(StudyRoot.nodes.get_or_none(uid=study_uid))

    def check_if_study_is_locked(self, study_uid: str) -> bool:
        root = StudyRoot.nodes.get_or_none(uid=study_uid)

        exceptions.NotFoundException.raise_if(root is None, "Study", study_uid)

        is_study_locked = (
            root.latest_locked.get_or_none() == root.latest_value.get_or_none()
        )
        return is_study_locked

    @classmethod
    def check_if_study_is_deleted(cls, study_uid: str) -> bool:
        root = StudyRoot.nodes.get_or_none(uid=study_uid)

        exceptions.NotFoundException.raise_if(root is None, "Study", study_uid)

        query = """
            MATCH (study_root:StudyRoot {uid: $uid})-[:LATEST]->(:StudyValue)<-[:BEFORE]-(:Delete)
            RETURN study_root
            """
        result, _ = db.cypher_query(query, {"uid": study_uid})
        return len(result) > 0 and len(result[0]) > 0

    @staticmethod
    def check_if_study_uid_and_version_exists(
        study_uid: str, study_value_version: str | None = None
    ) -> bool:
        if study_value_version:
            query = """
                MATCH (r:StudyRoot {uid: $uid})-[hv:HAS_VERSION]->(v:StudyValue)
                WHERE NOT (v)<-[:BEFORE]-(:Delete) AND hv.version=$version
                RETURN r
                """
        else:
            query = """
                MATCH (r:StudyRoot {uid: $uid})-[:LATEST]->(v:StudyValue)
                WHERE NOT (v)<-[:BEFORE]-(:Delete)
                RETURN r
                """

        result, _ = db.cypher_query(
            query, {"uid": study_uid, "version": study_value_version}
        )

        return len(result) > 0 and len(result[0]) > 0

    def get_latest_released_version_from_specific_datetime(
        self, study_uid: str, specified_datetime: str
    ) -> str | None:
        version_relationships = (
            StudyValue.nodes.fetch_relations("has_version")
            .filter(
                **{
                    "has_version|end_date__lte": datetime.fromisoformat(
                        specified_datetime
                    ),
                    "has_version|status": "RELEASED",
                    "has_version__uid": study_uid,
                }
            )
            .order_by("-has_version|end_date")
            .all()
        )

        if len(version_relationships) == 0:
            return None

        latest_version_relationship = version_relationships[0]
        return latest_version_relationship[2].version

    def _retrieve_study_subpart_with_history(
        self, uid: str, is_subpart: bool = False, study_value_version: str | None = None
    ) -> list[Any]:
        """
        returns the audit trail for all study subparts of the study
        """
        params: dict[str, str | list[str]] = {}
        if not is_subpart:
            params = {"study_uid": uid}
            if study_value_version:
                version = "{version: $study_value_version}"
                params["study_value_version"] = study_value_version
            else:
                version = ""

            subpart_uids = db.cypher_query(
                f"""
                MATCH (:StudyRoot {{uid: $study_uid}})-[:HAS_VERSION{version}]->(:StudyValue)
                -[:HAS_STUDY_SUBPART]->(:StudyValue)<-[:HAS_VERSION]-(ssr:StudyRoot)
                RETURN DISTINCT ssr.uid
                """,
                params=params,
            )
            subpart_uids = [subpart_uid[0] for subpart_uid in subpart_uids[0]]
        else:
            subpart_uids = [uid]

        params = {"subpart_uids": subpart_uids, "uid": uid}
        if study_value_version:
            version = "{version: $study_value_version}"
            params["study_value_version"] = study_value_version
        else:
            version = ""

        if not is_subpart and version:
            parent_in_version = f"<-[:HAS_STUDY_SUBPART]-(:StudyValue)<-[:HAS_VERSION{version}]-(:StudyRoot {{uid: $uid}})"
        else:
            parent_in_version = ""

        rs = db.cypher_query(
            f"""
            MATCH (ssr:StudyRoot)-[h_rel:HAS_VERSION]->(ssv:StudyValue)
            {parent_in_version}
            WHERE ssr.uid IN $subpart_uids
            OPTIONAL MATCH (ssv)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (ssv)<-[:BEFORE]-(bsa:StudyAction)
            OPTIONAL MATCH (ssv)<-[:HAS_STUDY_SUBPART]-(psv:StudyValue)<-[p_h_rel:HAS_VERSION]-(psr:StudyRoot)
            RETURN DISTINCT
                psr.uid AS parent_uid,
                ssr.uid AS subpart_uid,
                ssv.subpart_id AS subpart_id,
                ssv.study_acronym AS study_acronym,
                ssv.study_subpart_acronym AS study_subpart_acronym,
                h_rel.author_id AS author_id,
                h_rel.start_date AS start_date,
                h_rel.end_date AS end_date,
                labels(asa) AS change_type
                ORDER BY start_date DESC
            """,
            params=params,
        )
        rs = utils.db_result_to_list(rs)
        rs.reverse()

        result = []
        if not is_subpart:
            subpart_status = set()
            for item in rs:
                if item["parent_uid"] is not None and item["parent_uid"] != uid:
                    continue
                if item["subpart_uid"] not in subpart_status and not item["parent_uid"]:
                    continue

                if item["parent_uid"]:
                    subpart_status.add(item["subpart_uid"])
                    remove = False
                else:
                    remove = True

                change_type = ""
                for action in item["change_type"]:
                    if "StudyAction" not in action:
                        change_type = action

                if item["subpart_uid"] in subpart_status:
                    result.append(
                        {
                            "subpart_uid": item["subpart_uid"],
                            "subpart_id": (
                                item["subpart_id"] if item["parent_uid"] else None
                            ),
                            "study_acronym": (
                                item["study_acronym"] if item["parent_uid"] else None
                            ),
                            "study_subpart_acronym": (
                                item["study_subpart_acronym"]
                                if item["parent_uid"]
                                else None
                            ),
                            "start_date": convert_to_datetime(value=item["start_date"]),
                            "end_date": (
                                convert_to_datetime(value=item["end_date"])
                                if item["end_date"]
                                else None
                            ),
                            "author_username": item["author_id"],
                            "change_type": (
                                change_type if item["parent_uid"] else "Delete"
                            ),
                        }
                    )

                    if remove:
                        subpart_status.remove(item["subpart_uid"])
        else:
            for item in rs:
                for action in item["change_type"]:
                    if "StudyAction" not in action:
                        change_type = action

                result.append(
                    {
                        "subpart_uid": item["subpart_uid"],
                        "subpart_id": item["subpart_id"],
                        "study_acronym": item["study_acronym"],
                        "study_subpart_acronym": item["study_subpart_acronym"],
                        "start_date": convert_to_datetime(value=item["start_date"]),
                        "end_date": (
                            convert_to_datetime(value=item["end_date"])
                            if item["end_date"]
                            else None
                        ),
                        "author_username": item["author_id"],
                        "change_type": change_type,
                    }
                )

        result.reverse()

        return calculate_diffs(result, StudySubpartAuditTrail)

    def get_soa_preferences(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        field_names: Sequence[str] | None = None,
    ) -> list[StudyBooleanField]:
        """Gets StudyBooleanField nodes related to SoA preferences"""

        if field_names is None:
            field_names = settings.study_soa_preferences_fields

        filters: dict[str, Any]

        if study_value_version:
            filters = {
                "has_boolean_field__has_version__uid": study_uid,
                "has_boolean_field__has_version|version": study_value_version,
            }
        else:
            filters = {
                "has_boolean_field__latest_value__uid": study_uid,
            }

        filters["field_name__in"] = field_names
        nodes = (
            StudyBooleanField.nodes.fetch_relations(
                "has_after__audit_trail",
            )
            .filter(**filters)
            .resolve_subgraph()
        )
        return nodes

    def post_soa_preferences(
        self, study_uid: str, soa_preferences: StudySoaPreferencesInput
    ) -> list[StudyBooleanField]:
        """Creates StudyBooleanField nodes of SoA preferences if none are present"""

        exceptions.AlreadyExistsException.raise_if(
            self.get_soa_preferences(study_uid=study_uid),
            msg=f"SoA preferences already exist for Study with UID '{study_uid}'",
        )

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        for name, value in soa_preferences.dict(by_alias=True).items():
            field_sf = StudyBooleanField.create({"field_name": name, "value": value})[0]
            latest_study_value.has_boolean_field.connect(field_sf)

            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_after=field_sf,
                study_field_node_before=None,
                change_status=None,
                author_id=self.audit_info.author_id,
                date=datetime.now(timezone.utc),
            )

        return self.get_soa_preferences(study_uid=study_uid)

    def edit_soa_preferences(
        self,
        study_uid: str,
        soa_preferences: StudySoaPreferencesInput,
    ) -> list[StudyBooleanField]:
        """Replaces StudyBooleanField nodes of SoA preferences for the supplied show_* parameters only"""

        # exclude_unset skips properties that were not provided on init, also won't use defaults
        prefs = soa_preferences.dict(by_alias=True, exclude_unset=True)

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value = study_root.latest_value.single()

        nodes = self.get_soa_preferences(
            study_uid=study_uid, field_names=tuple(prefs.keys())
        )

        # disconnect the previous version from StudyValue
        for node in nodes:
            latest_study_value.has_boolean_field.disconnect(node)

        _nodes = {node.field_name: node for node in nodes}

        for name, value in prefs.items():
            field_sf = StudyBooleanField.create({"field_name": name, "value": value})[0]
            latest_study_value.has_boolean_field.connect(field_sf)

            self._generate_study_field_audit_node(
                study_root_node=study_root,
                study_field_node_after=field_sf,
                study_field_node_before=_nodes.get(name, None),
                change_status=None,
                author_id=self.audit_info.author_id,
                date=datetime.now(timezone.utc),
            )

        return self.get_soa_preferences(study_uid=study_uid)
