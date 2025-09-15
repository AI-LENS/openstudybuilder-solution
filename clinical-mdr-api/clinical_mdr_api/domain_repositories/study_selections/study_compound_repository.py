import datetime
from dataclasses import dataclass
from typing import Any

from neomodel import db
from neomodel.sync_.match import (
    Collect,
    NodeNameResolver,
    Optional,
    RelationNameResolver,
)

from clinical_mdr_api import utils
from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.models.compounds import CompoundAliasRoot
from clinical_mdr_api.domain_repositories.models.controlled_terminology import (
    CTTermRoot,
)
from clinical_mdr_api.domain_repositories.models.medicinal_product import (
    MedicinalProductRoot,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import (
    Create,
    Delete,
    Edit,
    StudyAction,
)
from clinical_mdr_api.domain_repositories.models.study_selections import StudyCompound
from clinical_mdr_api.domains.study_selections.study_selection_compound import (
    StudySelectionCompoundsAR,
    StudySelectionCompoundVO,
)
from common.exceptions import BusinessLogicException, NotFoundException
from common.utils import convert_to_datetime


@dataclass
class StudyCompoundSelectionHistory:
    """Class for selection history items"""

    study_selection_uid: str
    compound_uid: str | None
    compound_alias_uid: str | None
    medicinal_product_uid: str | None
    type_of_treatment_uid: str | None
    reason_for_missing_value_uid: str | None
    dispenser_uid: str | None
    dose_frequency_uid: str | None
    delivery_device_uid: str | None
    other_info: str | None
    start_date: datetime.datetime
    status: str | None
    author_id: str
    change_type: str
    end_date: datetime.datetime | None
    order: int


class StudySelectionCompoundRepository:

    def _retrieves_all_data(
        self,
        study_uid: str | None = None,
        study_value_version: str | None = None,
        project_name: str | None = None,
        project_number: str | None = None,
        type_of_treatment: str | None = None,
    ) -> tuple[StudySelectionCompoundVO]:
        query = ""
        query_parameters: dict[str, Any] = {}
        if study_uid:
            if study_value_version:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:HAS_VERSION { version: $version}]->(sv:StudyValue)"
                query_parameters["uid"] = study_uid
                query_parameters["version"] = study_value_version
            else:
                query = "MATCH (sr:StudyRoot { uid: $uid})-[l:LATEST]->(sv:StudyValue)"
                query_parameters["uid"] = study_uid
        else:
            query = "MATCH (sr:StudyRoot)-[l:LATEST]->(sv:StudyValue)"

        query += """
        -[:HAS_STUDY_COMPOUND]->(sc:StudyCompound)
        OPTIONAL MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)<-[:HAS_VERSION]-(car:CompoundAliasRoot)
        OPTIONAL MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)
        OPTIONAL MATCH (sc)-[:HAS_MEDICINAL_PRODUCT]->(:MedicinalProductValue)<-[:HAS_VERSION]-(mpr:MedicinalProductRoot)
        WITH DISTINCT sr, sv, sc, car, cr, mpr
        """

        if project_name is not None or project_number is not None:
            query += """
                MATCH (sv)-[:HAS_PROJECT]->(:StudyProjectField)<-[:HAS_FIELD]-(proj:Project)
                WITH sr, sv, sc, car, cr, mpr, proj
            """
            filter_list = []
            if project_name is not None:
                filter_list.append("proj.name=$project_name")
                query_parameters["project_name"] = project_name
            if project_number is not None:
                filter_list.append("proj.project_number=$project_number")
                query_parameters["project_number"] = project_number
            query += " WHERE "
            query += " AND ".join(filter_list)

        if type_of_treatment:
            query += """MATCH (sc)-[:HAS_TYPE_OF_TREATMENT]->(tot:CTTermRoot)
            -[:HAS_NAME_ROOT]->(:CTTermNameRoot)-->(:CTTermNameValue {name: $type_of_treatment})"""
            query_parameters["type_of_treatment"] = type_of_treatment
        else:
            query += " OPTIONAL MATCH (sc)-[:HAS_TYPE_OF_TREATMENT]->(tot:CTTermRoot)"

        query += """
            WITH DISTINCT sr, sv, sc, car, cr, mpr, tot
            OPTIONAL MATCH (sc)-[:HAS_DOSE_FREQUENCY]->(doseFrequency:CTTermRoot)
            OPTIONAL MATCH (sc)-[:HAS_DELIVERY_DEVICE]->(deliveryDevice:CTTermRoot)
            OPTIONAL MATCH (sc)-[:HAS_DISPENSED_IN]->(di:CTTermRoot)
            OPTIONAL MATCH (sc)-[:HAS_REASON_FOR_NULL_VALUE]->(nvr:CTTermRoot)
            OPTIONAL MATCH (sc)-[:STUDY_COMPOUND_HAS_COMPOUND_DOSING]->(scd:StudyCompoundDosing)<-[:HAS_STUDY_COMPOUND_DOSING]-(sv)

            MATCH (sc)<-[:AFTER]-(sa:StudyAction)

            WITH sr, sc, car, cr, mpr, tot, doseFrequency, deliveryDevice, di, nvr, scd, sa
            RETURN
                sr.uid AS study_uid,
                sc.uid AS study_compound_uid,
                sc.order AS order,
                sc.other_information AS other_information,
                cr.uid AS compound_uid,
                car.uid AS compound_alias_uid,
                mpr.uid AS medicinal_product_uid,
                tot.uid AS type_of_treatment_uid,
                doseFrequency.uid AS dose_frequency_uid,
                deliveryDevice.uid AS delivery_device_uid,
                di.uid AS dispenser_uid,
                nvr.uid AS reason_for_missing,
                count(scd) AS study_compound_dosing_count,
                sa.date AS start_date,
                sa.author_id AS author_id
                ORDER BY order
            """
        all_compound_selections = db.cypher_query(query, query_parameters)
        all_selections = []
        for selection in utils.db_result_to_list(all_compound_selections):
            selection_vo = StudySelectionCompoundVO.from_input_values(
                study_uid=selection["study_uid"],
                other_info=selection["other_information"],
                compound_uid=selection["compound_uid"],
                compound_alias_uid=selection["compound_alias_uid"],
                medicinal_product_uid=selection["medicinal_product_uid"],
                type_of_treatment_uid=selection["type_of_treatment_uid"],
                dose_frequency_uid=selection["dose_frequency_uid"],
                delivery_device_uid=selection["delivery_device_uid"],
                dispenser_uid=selection["dispenser_uid"],
                reason_for_missing_value_uid=selection["reason_for_missing"],
                study_compound_dosing_count=selection["study_compound_dosing_count"],
                study_selection_uid=selection["study_compound_uid"],
                start_date=convert_to_datetime(value=selection["start_date"]),
                author_id=selection["author_id"],
            )
            all_selections.append(selection_vo)
        return tuple(all_selections)

    def find_all(
        self,
        project_name: str | None = None,
        project_number: str | None = None,
        type_of_treatment: str | None = None,
    ) -> list[StudySelectionCompoundsAR]:
        """
        Finds all the selected study compounds for all studies, and create the aggregate
        :return: List of StudySelectionCompoundsAR, potentially empty
        """
        all_selections = self._retrieves_all_data(
            project_name=project_name,
            project_number=project_number,
            type_of_treatment=type_of_treatment,
        )
        # Create a dictionary, with study_uid as key, and list of selections as value
        selection_aggregate_dict: dict[Any, Any] = {}
        selection_aggregates = []
        for selection in all_selections:
            if selection.study_uid in selection_aggregate_dict:
                selection_aggregate_dict[selection.study_uid].append(selection)
            else:
                selection_aggregate_dict[selection.study_uid] = [selection]
        # Then, create the list of VO from the dictionary
        for study_uid, selections in selection_aggregate_dict.items():
            selection_aggregates.append(
                StudySelectionCompoundsAR.from_repository_values(
                    study_uid=study_uid, study_compounds_selection=selections
                )
            )
        return selection_aggregates

    def find_by_study(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
        **filters,
    ) -> StudySelectionCompoundsAR:
        """
        Finds all the selected study compounds for a given study, and creates the aggregate
        :param study_uid:
        :param study_value_version:
        :param for_update:
        :return:
        """
        if for_update:
            acquire_write_lock_study_value(study_uid)
        all_selections = self._retrieves_all_data(
            study_uid, study_value_version, **filters
        )
        selection_aggregate = StudySelectionCompoundsAR.from_repository_values(
            study_uid=study_uid, study_compounds_selection=all_selections
        )
        if for_update:
            selection_aggregate.repository_closure_data = all_selections
        return selection_aggregate

    def find_by_uid(
        self,
        study_uid: str,
        study_compound_uid: str,
        study_value_version: str | None = None,
    ) -> tuple[StudySelectionCompoundVO, int]:
        """Find a study compound by its UID."""
        query_parameters = {
            "study_uid": study_uid,
            "study_compound_uid": study_compound_uid,
        }
        if study_value_version:
            query = "MATCH (sr:StudyRoot {uid: $study_uid})-[l:HAS_VERSION {status:'RELEASED', version: $version}]->(sv:StudyValue)"
            query_parameters["version"] = study_value_version
        else:
            query = "MATCH (sr:StudyRoot {uid: $study_uid})-[l:LATEST]->(sv:StudyValue)"
        query += """
        -[:HAS_STUDY_COMPOUND]->(sc:StudyCompound {uid: $study_compound_uid})
        OPTIONAL MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)<-[:LATEST]-(car:CompoundAliasRoot)
        OPTIONAL MATCH (sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)
        OPTIONAL MATCH (sc)-[:HAS_MEDICINAL_PRODUCT]->(:MedicinalProductValue)<-[:HAS_VERSION]-(mpr:MedicinalProductRoot)
        WITH DISTINCT sr, sv, sc, car, cr, mpr
        OPTIONAL MATCH (sc)-[:HAS_TYPE_OF_TREATMENT]->(tot:CTTermRoot)
        WITH DISTINCT sr, sv, sc, car, cr, mpr, tot
        OPTIONAL MATCH (sc)-[:HAS_DOSE_FREQUENCY]->(doseFrequency:CTTermRoot)
        OPTIONAL MATCH (sc)-[:HAS_DELIVERY_DEVICE]->(deliveryDevice:CTTermRoot)
        OPTIONAL MATCH (sc)-[:HAS_DISPENSED_IN]->(di:CTTermRoot)
        OPTIONAL MATCH (sc)-[:HAS_REASON_FOR_NULL_VALUE]->(nvr:CTTermRoot)
        OPTIONAL MATCH (sc)-[:STUDY_COMPOUND_HAS_COMPOUND_DOSING]->(scd)<-[:HAS_STUDY_COMPOUND_DOSING]-(sv)
        MATCH (sc)<-[:AFTER]-(sa:StudyAction)

        WITH sr, sc, car, cr, mpr, tot, doseFrequency, deliveryDevice, di, nvr, scd, sa
        RETURN
            sr.uid AS study_uid,
            sc.uid AS study_compound_uid,
            sc.order AS order,
            sc.other_information AS other_information,
            cr.uid AS compound_uid,
            car.uid AS compound_alias_uid,
            mpr.uid AS medicinal_product_uid,
            tot.uid AS type_of_treatment_uid,
            doseFrequency.uid AS dose_frequency_uid,
            deliveryDevice.uid AS delivery_device_uid,
            di.uid AS dispenser_uid,
            nvr.uid AS reason_for_missing,
            count(scd) AS study_compound_dosing_count,
            sa.date AS start_date,
            sa.author_id AS author_id
            ORDER BY order
        """

        result = db.cypher_query(query, query_parameters)
        result = utils.db_result_to_list(result)
        NotFoundException.raise_if(
            len(result) == 0,
            msg=f"Study Compound with UID '{study_compound_uid}' doesn't exist for Study with UID '{study_uid}'",
        )
        assert (
            len(result) == 1
        ), f"Found more than 1 study compound with uid {study_compound_uid}"
        selection = result[0]
        selection_vo = StudySelectionCompoundVO.from_input_values(
            study_uid=selection["study_uid"],
            other_info=selection["other_information"],
            compound_uid=selection["compound_uid"],
            compound_alias_uid=selection["compound_alias_uid"],
            medicinal_product_uid=selection["medicinal_product_uid"],
            type_of_treatment_uid=selection["type_of_treatment_uid"],
            dose_frequency_uid=selection["dose_frequency_uid"],
            delivery_device_uid=selection["delivery_device_uid"],
            dispenser_uid=selection["dispenser_uid"],
            reason_for_missing_value_uid=selection["reason_for_missing"],
            study_compound_dosing_count=selection["study_compound_dosing_count"],
            study_selection_uid=selection["study_compound_uid"],
            start_date=convert_to_datetime(value=selection["start_date"]),
            author_id=selection["author_id"],
        )
        return selection_vo, selection["order"]

    def _get_audit_node(
        self, study_selection: StudySelectionCompoundsAR, study_selection_uid: str
    ):
        all_current_ids = []
        for item in study_selection.study_compounds_selection:
            all_current_ids.append(item.study_selection_uid)
        all_closure_ids = []
        for item in study_selection.repository_closure_data:
            all_closure_ids.append(item.study_selection_uid)
        # if uid is in current data
        if study_selection_uid in all_current_ids:
            # if uid is in closure data
            if study_selection_uid in all_closure_ids:
                return Edit()
            return Create()
        return Delete()

    def save(self, study_selection: StudySelectionCompoundsAR, author_id: str) -> None:
        """
        Persist the set of selected study compounds from the aggregate to the database
        :param study_selection:
        """

        assert study_selection.repository_closure_data is not None

        # get the closure_data
        closure_data = study_selection.repository_closure_data
        closure_data_length = len(closure_data)

        # getting the latest study value node
        study_root_node = StudyRoot.nodes.get(uid=study_selection.study_uid)
        latest_study_value_node = study_root_node.latest_value.single()

        BusinessLogicException.raise_if(
            study_root_node.latest_locked.get_or_none() == latest_study_value_node,
            msg="You cannot add or reorder a study selection when the study is in a locked state.",
        )

        selections_to_remove = []
        selections_to_add = []

        # check if object is removed from the selection list - delete have been called
        if len(closure_data) > len(study_selection.study_compounds_selection):
            # remove the last item from old list, as there will no longer be any study objective with that high order
            selections_to_remove.append((len(closure_data), closure_data[-1]))

        # loop through new data - start=1 as order starts at 1 not at 0 and find what needs to be removed and added
        for order, selection in enumerate(
            study_selection.study_compounds_selection, start=1
        ):
            # check whether something new is added
            if closure_data_length > order - 1:
                # check if anything has changed
                if selection is not closure_data[order - 1]:
                    # update the selection by removing the old if the old exists, and adding new selection
                    selections_to_remove.append((order, closure_data[order - 1]))
                    selections_to_add.append((order, selection))
            else:
                # else something new have been added
                selections_to_add.append((order, selection))

        # audit trail nodes dictionary, holds the new nodes created for the audit trail
        audit_trail_nodes = {}

        # loop through and remove selections
        for order, selection in selections_to_remove:
            last_study_selection_node = latest_study_value_node.has_study_compound.get(
                uid=selection.study_selection_uid
            )
            self._remove_old_selection_if_exists(study_selection.study_uid, selection)
            audit_node = self._get_audit_node(
                study_selection, selection.study_selection_uid
            )
            audit_node = self._set_before_audit_info(
                audit_node,
                last_study_selection_node,
                study_root_node,
                author_id,
            )
            audit_trail_nodes[selection.study_selection_uid] = audit_node
            if isinstance(audit_node, Delete):
                self._add_new_selection(
                    latest_study_value_node, order, selection, audit_node, True
                )

        # loop through and add selections
        for order, selection in selections_to_add:
            if selection.study_selection_uid in audit_trail_nodes:
                audit_node = audit_trail_nodes[selection.study_selection_uid]
            else:
                audit_node = Create()
                audit_node.author_id = selection.author_id
                audit_node.date = selection.start_date
                audit_node.save()
                study_root_node.audit_trail.connect(audit_node)
            self._add_new_selection(
                latest_study_value_node, order, selection, audit_node, False
            )

    @staticmethod
    def _remove_old_selection_if_exists(
        study_uid: str, study_selection: StudySelectionCompoundVO
    ) -> None:
        """
        Removal is taking both new and old uid. When a study selection is deleted, we do no longer need to use the uid
        on that study selection node anymore, however do to database constraint the node needs to have a uid. So we are
        overwriting a deleted node uid, with a new never used dummy uid.

        We are doing this to be able to maintain the selection instead of removing it, instead a removal will only
        detach the selection from the study value node. So we keep the old selection to have full audit trail available
        in the database.
        :param study_uid:
        :param study_selection:
        :return:
        """
        db.cypher_query(
            """
            MATCH (:StudyRoot { uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_COMPOUND]->(se:StudyCompound { uid: $selection_uid})
            DELETE rel
            """,
            {
                "study_uid": study_uid,
                "selection_uid": study_selection.study_selection_uid,
            },
        )

    # TODO FIX StudyObjectiveSelection
    @staticmethod
    def _set_before_audit_info(
        audit_node: StudyAction,
        study_objective_selection_node: StudyCompound,
        study_root_node: StudyRoot,
        author_id: str,
    ) -> StudyAction:
        audit_node.author_id = author_id
        audit_node.date = datetime.datetime.now(datetime.timezone.utc)
        audit_node.save()

        audit_node.has_before.connect(study_objective_selection_node)
        study_root_node.audit_trail.connect(audit_node)
        return audit_node

    @staticmethod
    def _add_new_selection(
        latest_study_value_node: StudyValue,
        order: int,
        selection: StudySelectionCompoundVO,
        audit_node: StudyAction,
        for_deletion: bool = False,
    ):
        # Create new compound selection
        study_compound_selection_node = StudyCompound(order=order).save()
        study_compound_selection_node.uid = selection.study_selection_uid
        # Check if there is any other information
        if selection.other_info:
            study_compound_selection_node.other_information = selection.other_info
        study_compound_selection_node.save()
        # Connect new node with study value
        if not for_deletion:
            # Connect new node with study value
            latest_study_value_node.has_study_compound.connect(
                study_compound_selection_node
            )
        # Connect new node with audit trail
        audit_node.has_after.connect(study_compound_selection_node)

        # check if compound alias is set
        if selection.compound_alias_uid:
            # find the compound alias value
            compound_alias_root_node = CompoundAliasRoot.nodes.get(
                uid=selection.compound_alias_uid
            )
            latest_compound_alias_value_node = (
                compound_alias_root_node.latest_final.single()
            )
            # Connect new node with compound alias value
            study_compound_selection_node.has_selected_compound.connect(
                latest_compound_alias_value_node
            )

        if selection.medicinal_product_uid:
            # Find the latest medicinal product value
            medicinal_product_root_node = MedicinalProductRoot.nodes.get(
                uid=selection.medicinal_product_uid
            )
            latest_medicinal_product_value_node = (
                medicinal_product_root_node.latest_final.single()
            )
            # Connect new node with medicinal product value
            study_compound_selection_node.has_medicinal_product.connect(
                latest_medicinal_product_value_node
            )
            dose_frequency = (
                latest_medicinal_product_value_node.has_dose_frequency.single()
            )
            if dose_frequency:
                study_compound_selection_node.has_dose_frequency.connect(dose_frequency)

            delivery_device = (
                latest_medicinal_product_value_node.has_delivery_device.single()
            )
            if delivery_device:
                study_compound_selection_node.has_delivery_device.connect(
                    delivery_device
                )

            dispenser = latest_medicinal_product_value_node.has_dispenser.single()
            if dispenser:
                study_compound_selection_node.has_dispenser.connect(dispenser)

            # Find the latest pharmaceutical product value connected to the medicinal product root
            pharmaceutical_product_root_nodes = (
                latest_medicinal_product_value_node.has_pharmaceutical_product.all()
            )

            for pharmaceutical_product_root_node in pharmaceutical_product_root_nodes:
                latest_pharmaceutical_product_value_node = (
                    pharmaceutical_product_root_node.latest_final.single()
                )
                # Connect new node with pharmaceutical product value
                if latest_pharmaceutical_product_value_node:
                    study_compound_selection_node.has_pharmaceutical_product.connect(
                        latest_pharmaceutical_product_value_node
                    )

        # check if type of treatment is set
        if selection.type_of_treatment_uid:
            # find the type of treatment
            type_of_treatment_node = CTTermRoot.nodes.get_or_none(
                uid=selection.type_of_treatment_uid
            )

            NotFoundException.raise_if(
                type_of_treatment_node is None,
                "CT Term for 'type of treatment'",
                selection.type_of_treatment_uid,
            )

            # Connect new node with type_of_treatment node
            study_compound_selection_node.has_type_of_treatment.connect(
                type_of_treatment_node
            )

        # check if reason_for_missing_value_uid is set
        if selection.reason_for_missing_value_uid:
            # check if reason_for_missing exists
            null_value_reason_node = CTTermRoot.nodes.get_or_none(
                uid=selection.reason_for_missing_value_uid
            )

            NotFoundException.raise_if(
                null_value_reason_node is None,
                "CT Term for 'reason for missing'",
                selection.reason_for_missing_value_uid,
            )

            # connect to reason_for_missing node
            study_compound_selection_node.has_reason_for_missing.connect(
                null_value_reason_node
            )

    def generate_uid(self) -> str:
        return StudyCompound.get_next_free_uid_and_increment_counter()

    def _get_selection_with_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ):
        """
        returns the audit trail for study compounds either for a specific selection or for all study compounds for the study
        """
        if study_selection_uid:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(sc:StudyCompound { uid: $study_selection_uid})
            WITH distinct(sc) as all_sc
            """
        else:
            cypher = """
            MATCH (sr:StudyRoot { uid: $study_uid})-[:AUDIT_TRAIL]->(:StudyAction)-[:BEFORE|AFTER]->(all_sc:StudyCompound)
            WITH DISTINCT all_sc
            """
        compound_selections_audit_trail = db.cypher_query(
            cypher
            + """
            OPTIONAL MATCH (all_sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)-[:IS_COMPOUND]->(cr:CompoundRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_SELECTED_COMPOUND]->(:CompoundAliasValue)<-[:LATEST]-(car:CompoundAliasRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_MEDICINAL_PRODUCT]->(:MedicinalProductValue)<-[:HAS_VERSION]-(mpr:MedicinalProductRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_TYPE_OF_TREATMENT]->(tot:CTTermRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_DOSE_FREQUENCY]->(doseFrequency:CTTermRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_DELIVERY_DEVICE]->(deliveryDevice:CTTermRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_DISPENSED_IN]->(di:CTTermRoot)
            OPTIONAL MATCH (all_sc)-[:HAS_REASON_FOR_NULL_VALUE]->(nvr:CTTermRoot)
            
            MATCH (all_sc)<-[:AFTER]-(asa:StudyAction)
            OPTIONAL MATCH (all_sc)<-[:BEFORE]-(bsa:StudyAction)

            WITH all_sc, cr, car, tot, mpr, doseFrequency, deliveryDevice, di, nvr, asa, bsa
            ORDER BY all_sc.uid, asa.date DESC
            RETURN
                all_sc.uid AS study_selection_uid,
                all_sc.order AS order,
                all_sc.other_information AS other_information,
                cr.uid AS compound_uid,
                car.uid AS compound_alias_uid,
                mpr.uid AS medicinal_product_uid,
                tot.uid AS type_of_treatment_uid,
                doseFrequency.uid AS dose_frequency_uid,
                deliveryDevice.uid AS delivery_device_uid,
                di.uid AS dispenser_uid,
                deliveryDevice.uid AS device_uid,
                nvr.uid AS reason_for_missing,
                asa.date AS start_date,
                asa.author_id AS author_id,
                asa.status AS status,
                labels(asa) AS change_type,
                bsa.date AS end_date
""",
            {"study_uid": study_uid, "study_selection_uid": study_selection_uid},
        )
        result = []
        for res in utils.db_result_to_list(compound_selections_audit_trail):
            change_type = ""
            for action in res["change_type"]:
                if "StudyAction" not in action:
                    change_type = action
            if res["end_date"]:
                end_date = convert_to_datetime(value=res["end_date"])
            else:
                end_date = None
            result.append(
                StudyCompoundSelectionHistory(
                    study_selection_uid=res["study_selection_uid"],
                    compound_uid=res["compound_uid"],
                    compound_alias_uid=res["compound_alias_uid"],
                    medicinal_product_uid=res["medicinal_product_uid"],
                    other_info=res["other_information"],
                    type_of_treatment_uid=res["type_of_treatment_uid"],
                    dose_frequency_uid=res["dose_frequency_uid"],
                    delivery_device_uid=res["delivery_device_uid"],
                    dispenser_uid=res["dispenser_uid"],
                    reason_for_missing_value_uid=res["reason_for_missing"],
                    order=res["order"],
                    start_date=convert_to_datetime(value=res["start_date"]),
                    status=res["status"],
                    author_id=res["author_id"],
                    change_type=change_type,
                    end_date=end_date,
                )
            )
        return result

    def find_selection_history(
        self, study_uid: str, study_selection_uid: str | None = None
    ) -> list[StudyCompoundSelectionHistory]:
        """
        Simple method to return all versions of a study objectives for a study.
        Optionally a specific selection uid is given to see only the response for a specific selection.
        """
        if study_selection_uid:
            return self._get_selection_with_history(
                study_uid=study_uid, study_selection_uid=study_selection_uid
            )
        return self._get_selection_with_history(study_uid=study_uid)

    def close(self) -> None:
        # Our repository guidelines state that repos should have a close method
        # But nothing needs to be done in this one
        pass

    def get_selection_uid_by_details(
        self, study_compound: StudySelectionCompoundVO
    ) -> str | None:
        query = """
            MATCH (:StudyRoot {uid: $study_uid})-[:LATEST]->(:StudyValue)-[rel:HAS_STUDY_COMPOUND]->
                    (sc:StudyCompound)-[HAS_SELECTED_COMPOUND]->(cav:CompoundAliasValue)<-[:LATEST]-(car:CompoundAliasRoot {uid: $compound_alias_uid})
            WITH *
            MATCH (sc)-[:HAS_MEDICINAL_PRODUCT]->(:MedicinalProductValue)<-[:HAS_VERSION]-(mpr:MedicinalProductRoot {uid: $medicinal_product_uid})
            WITH *
            MATCH (sc)-[:HAS_DELIVERY_DEVICE]->(deliveryDevice:CTTermRoot {uid: $delivery_device_uid})
            WITH *
            MATCH (sc)-[:HAS_DOSE_FREQUENCY]->(doseFrequency:CTTermRoot {uid: $dose_frequency_uid})
            WITH *
            MATCH (sc)-[:HAS_DISPENSED_IN]->(dispenser:CTTermRoot {uid: $dispenser_uid})
            RETURN sc
            """
        result, _ = db.cypher_query(
            query,
            {
                "study_uid": study_compound.study_uid,
                "compound_alias_uid": study_compound.compound_alias_uid,
                "medicinal_product_uid": study_compound.medicinal_product_uid,
                "delivery_device_uid": study_compound.delivery_device_uid,
                "dose_frequency_uid": study_compound.dose_frequency_uid,
                "dispenser_uid": study_compound.dispenser_uid,
                "device_uid": study_compound.delivery_device_uid,
            },
        )
        if len(result) > 0 and len(result[0]) > 0:
            return result[0][0].get("uid")
        return None

    @staticmethod
    def get_compound_uid_to_arm_uids_mapping(study_uid: str) -> dict[str, set[str]]:
        results = (
            StudyRoot.nodes.fetch_relations(
                Optional(
                    "latest_value__has_study_compound__has_compound_dosing__study_element__has_design_cell__study_arm"
                )
            )
            .filter(uid=study_uid)
            .annotate(
                Collect(NodeNameResolver("latest_value"), distinct=True),
                Collect(RelationNameResolver("latest_value"), distinct=True),
                Collect(
                    NodeNameResolver("latest_value__has_study_compound"), distinct=True
                ),
                Collect(
                    RelationNameResolver("latest_value__has_study_compound"),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing__study_element"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing__study_element"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing__study_element__has_design_cell"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing__study_element__has_design_cell"
                    ),
                    distinct=True,
                ),
                Collect(
                    NodeNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing__study_element__has_design_cell__study_arm"
                    ),
                    distinct=True,
                ),
                Collect(
                    RelationNameResolver(
                        "latest_value__has_study_compound__has_compound_dosing__study_element__has_design_cell__study_arm"
                    ),
                    distinct=True,
                ),
            )
            .resolve_subgraph()
        )

        if not results:
            return {}

        return {
            compound.uid: {
                arm.uid
                for dosing in compound.has_compound_dosing
                for element in dosing.study_element
                for cell in element.has_design_cell
                for arm in cell.study_arm
            }
            for compound in results[0].latest_value[0].has_study_compound
        }
