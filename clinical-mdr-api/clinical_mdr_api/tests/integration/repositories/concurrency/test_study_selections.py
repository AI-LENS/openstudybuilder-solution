import unittest

import pytest
from neomodel import db

from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_attributes_repository import (
    CTTermAttributesRepository,
)
from clinical_mdr_api.domain_repositories.controlled_terminologies.ct_term_name_repository import (
    CTTermNameRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_title.study_title_repository import (
    StudyTitleRepository,
)
from clinical_mdr_api.domain_repositories.study_selections.study_objective_repository import (
    StudySelectionObjectiveRepository,
)
from clinical_mdr_api.domain_repositories.syntax_instances.objective_repository import (
    ObjectiveRepository,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_attributes import (
    CTTermAttributesAR,
    CTTermAttributesVO,
)
from clinical_mdr_api.domains.controlled_terminologies.ct_term_name import (
    CTTermCodelistVO,
    CTTermNameAR,
    CTTermNameVO,
)
from clinical_mdr_api.domains.libraries.object import (
    ParameterTermEntryVO,
    ParametrizedTemplateVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.registry_identifiers import (
    RegistryIdentifiersVO,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyDescriptionVO,
    StudyIdentificationMetadataVO,
)
from clinical_mdr_api.domains.study_selections.study_selection_objective import (
    StudySelectionObjectiveVO,
)
from clinical_mdr_api.domains.syntax_instances.objective import ObjectiveAR
from clinical_mdr_api.domains.syntax_templates.objective_template import (
    ObjectiveTemplateAR,
)
from clinical_mdr_api.domains.syntax_templates.template import TemplateVO
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    LibraryVO,
)
from clinical_mdr_api.services._meta_repository import MetaRepository
from clinical_mdr_api.tests.integration.repositories.concurrency.tools.optimistic_locking_validator import (
    OptimisticLockingValidator,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
    STARTUP_STUDY_FIELD_CYPHER,
    inject_base_data,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.domain.utils import AUTHOR_ID
from clinical_mdr_api.utils import strip_html
from common import exceptions


@pytest.mark.forked
class StudySelectionsConcurrencyTests(unittest.TestCase):
    """
    Tests for the following two cases:
    - The study (and selected nodes) are locked when creating/modifying/deleting a new study selection.
    - The study (and selected nodes) are locked when reordering a new study selection.
    """

    _repos = MetaRepository()

    library_name = "Sponsor"
    author_id = "TEST"
    template_name = "Example Template"
    parameter_terms: list[ParameterTermEntryVO] = []
    study_title_repository: StudyTitleRepository
    studies_repository: StudyDefinitionRepository
    ct_term_attributes_repository: CTTermAttributesRepository
    ct_term_names_repository: CTTermNameRepository
    study_objective_selection_repository: StudySelectionObjectiveRepository
    objective_repository: ObjectiveRepository

    ct_term_attributes_ar: CTTermAttributesAR
    ct_term_name_ar: CTTermNameAR
    parameterized_template_vo: ParametrizedTemplateVO
    object_ar: ObjectiveAR
    study_ar: StudyDefinitionAR | None

    # These are set as part of the test for [Objective, Endpoint, Timeframe]
    template_uid = None
    object_uid = None
    template_repository = None
    object_repository = None

    def setUp(self):
        inject_and_clear_db("concurrency.studyselections")
        inject_base_data()

    def set_up_base_graph_for_studies(self):
        db.cypher_query("MATCH (n) DETACH DELETE n")
        db.cypher_query(STARTUP_STUDY_FIELD_CYPHER)
        db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)
        db.cypher_query("CREATE CONSTRAINT FOR (n:CTTermRoot) REQUIRE n.uid IS UNIQUE;")

        self.study_title_repository = self._repos.study_title_repository
        self.studies_repository = self._repos.study_definition_repository
        self.ct_term_attributes_repository = self._repos.ct_term_attributes_repository
        self.ct_term_names_repository = self._repos.ct_term_name_repository
        self.study_objective_selection_repository = (
            self._repos.study_objective_repository
        )
        self.objective_repository = self._repos.objective_repository

        codelist_uid = "editable_cr"

        with db.transaction:
            study_ar = StudyDefinitionAR.from_initial_values(
                generate_uid_callback=lambda: "Study_000001",
                initial_id_metadata=StudyIdentificationMetadataVO.from_input_values(
                    project_number="456",
                    study_acronym="STUDY_ACR",
                    study_number=TestUtils.get_study_number(),
                    subpart_id=None,
                    description="123description",
                    registry_identifiers=RegistryIdentifiersVO.from_input_values(
                        ct_gov_id="CT_GOV_ID",
                        eudract_id="EUDRACT_ID",
                        universal_trial_number_utn="UTN",
                        japanese_trial_registry_id_japic="JAPIC",
                        investigational_new_drug_application_number_ind="IND",
                        eu_trial_number="ETN",
                        civ_id_sin_number="CISN",
                        national_clinical_trial_number="NCTN",
                        japanese_trial_registry_number_jrct="JRCT",
                        national_medical_products_administration_nmpa_number="NMPA",
                        eudamed_srn_number="ESN",
                        investigational_device_exemption_ide_number="IDE",
                        ct_gov_id_null_value_code=None,
                        eudract_id_null_value_code=None,
                        universal_trial_number_utn_null_value_code=None,
                        japanese_trial_registry_id_japic_null_value_code=None,
                        investigational_new_drug_application_number_ind_null_value_code=None,
                        eu_trial_number_null_value_code=None,
                        civ_id_sin_number_null_value_code=None,
                        national_clinical_trial_number_null_value_code=None,
                        japanese_trial_registry_number_jrct_null_value_code=None,
                        national_medical_products_administration_nmpa_number_null_value_code=None,
                        eudamed_srn_number_null_value_code=None,
                        investigational_device_exemption_ide_number_null_value_code=None,
                    ),
                ),
                project_exists_callback=lambda _: True,
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                study_number_exists_callback=lambda x, y: False,
                author_id=AUTHOR_ID,
            )
            self.studies_repository.save(study_ar)

            # update study_title because it has to be set before locking
            study = self.studies_repository.find_by_uid(study_ar.uid, for_update=True)
            study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=AUTHOR_ID,
            )
            self.studies_repository.save(study)

        # add CT terms that the study depends on
        terms = [
            "C49802",
            "C49703",
            "C49698",
            "C16153",
            "C139274",
            "C146995",
            "C126070",
            "C98737",
            "C123632",
            "C123631",
            "C126059",
            "C25196",
            "C49693",
            "C49694",
            "C98783",
            "C49697",
            "C117961",
            "C123630",
            "C123629",
            "C98715",
        ]
        for term in terms:
            self.create_and_approve_term(codelist_uid=codelist_uid, term_uid=term)

    def create_and_approve_term(self, codelist_uid, term_uid):
        with db.transaction:
            library_name = "Sponsor"
            library_vo = LibraryVO.from_repository_values(
                library_name=library_name, is_editable=True
            )

            ct_term_attributes_vo = CTTermAttributesVO.from_repository_values(
                codelists=[
                    CTTermCodelistVO(
                        codelist_uid=codelist_uid,
                        order=1,
                        library_name=self.library_name,
                    )
                ],
                catalogue_name="SDTM CT",
                concept_id=None,
                code_submission_value="code_submission_value",
                name_submission_value="name_submission_value",
                preferred_term="preferred_term",
                definition="definition",
            )

            self.ct_term_attributes_ar = CTTermAttributesAR.from_input_values(
                generate_uid_callback=lambda: term_uid,
                ct_term_attributes_vo=ct_term_attributes_vo,
                library=library_vo,
                author_id=AUTHOR_ID,
            )
            self.ct_term_attributes_repository.save(self.ct_term_attributes_ar)
        with db.transaction:
            ct_term_attributes_ar = self.ct_term_attributes_repository.find_by_uid(
                term_uid, for_update=True
            )
            ct_term_attributes_ar.approve(author_id=AUTHOR_ID)
            self.ct_term_attributes_repository.save(ct_term_attributes_ar)
        with db.transaction:
            ct_term_name_vo = CTTermNameVO.from_repository_values(
                codelists=[
                    CTTermCodelistVO(
                        codelist_uid=codelist_uid,
                        order=1,
                        library_name=self.library_name,
                    )
                ],
                catalogue_name="SDTM CT",
                name="StudyTitle",
                name_sentence_case="study_title",
            )

            self.ct_term_name_ar = CTTermNameAR.from_input_values(
                generate_uid_callback=lambda: term_uid,
                ct_term_name_vo=ct_term_name_vo,
                library=library_vo,
                author_id=AUTHOR_ID,
            )

            self.ct_term_names_repository.save(self.ct_term_name_ar)
        with db.transaction:
            ct_term_name_ar = self.ct_term_names_repository.find_by_uid(
                term_uid, for_update=True
            )
            ct_term_name_ar.approve(author_id=AUTHOR_ID)
            self.ct_term_names_repository.save(ct_term_name_ar)

    def set_up_base_graph_for_objectives_without_clearing_graph(self):
        self.template_uid = "ObjectiveTemplate_000002"
        self.object_uid = "Objective_000001"
        self.template_repository = self._repos.objective_template_repository
        self.object_repository = self._repos.objective_repository
        # Set up the base data
        template_vo = TemplateVO.from_repository_values(
            template_name=self.template_name,
            template_name_plain=strip_html(self.template_name),
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        objective_template_ar = ObjectiveTemplateAR.from_input_values(
            author_id=self.author_id,
            template=template_vo,
            library=library_vo,
            generate_uid_callback=lambda: self.template_uid,
        )
        # Create template
        with db.transaction:
            self.template_repository.save(objective_template_ar)
        # Approve template
        with db.transaction:
            objective_template_ar = self.template_repository.find_by_uid(
                self.template_uid, for_update=True
            )
            objective_template_ar.approve(author_id=self.author_id)
            self.template_repository.save(objective_template_ar)
        self.parameterized_template_vo = (
            ParametrizedTemplateVO.from_name_and_parameter_terms(
                name=self.template_name,
                template_uid=self.template_uid,
                parameter_terms=self.parameter_terms,
                library_name=objective_template_ar.library.name,
            )
        )
        library_vo = LibraryVO.from_input_values_2(
            library_name="Sponsor", is_library_editable_callback=lambda _: True
        )
        self.object_ar = ObjectiveAR.from_input_values(
            author_id=self.author_id,
            template=self.parameterized_template_vo,
            library=library_vo,
        )
        self.object_repository.save(self.object_ar)

    def test_study_selection_create_cancelled_on_concurrent_study_lock(self):
        self.set_up_base_graph_for_studies()
        self.set_up_base_graph_for_objectives_without_clearing_graph()

        with self.assertRaises(exceptions.BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.lock_study_without_save,
                concurrent_operation=self.create_study_objective_with_save,
                main_operation_after=self.save_study,
            )
        self.assertEqual(
            "You cannot add or reorder a study selection when the study is in a locked state.",
            message.exception.msg,
        )

    def test_study_selection_reorder_cancelled_on_concurrent_study_lock(self):
        self.set_up_base_graph_for_studies()
        self.set_up_base_graph_for_objectives_without_clearing_graph()

        with db.transaction:
            self.create_study_objective_with_save()

        with self.assertRaises(exceptions.BusinessLogicException) as message:
            OptimisticLockingValidator().assert_optimistic_locking_ensures_execution_order(
                main_operation_before=self.lock_study_without_save,
                concurrent_operation=self.reorder_study_objective_with_save,
                main_operation_after=self.save_study,
            )
        self.assertEqual(
            "You cannot add or reorder a study selection when the study is in a locked state.",
            message.exception.msg,
        )

    def lock_study_without_save(self):
        self.study_ar = self.studies_repository.find_by_uid(
            "Study_000001", for_update=True
        )
        self.study_ar.lock(version_description="info", author_id=AUTHOR_ID)

    def save_study(self):
        self.studies_repository.save(self.study_ar)

    def create_study_objective_with_save(self):
        # Load aggregate
        selection_aggregate = self.study_objective_selection_repository.find_by_study(
            study_uid="Study_000001", for_update=True
        )
        objective_repo = self.objective_repository
        self._repos.ct_term_name_repository.term_specific_order_by_uid(
            uid="term_root_final"
        )
        # create new VO to add
        new_selection = StudySelectionObjectiveVO.from_input_values(
            objective_uid="Objective_000001",
            objective_version="1.0",
            objective_level_uid="term_root_final",
            objective_level_order=1,
            author_id=AUTHOR_ID,
            study_selection_uid="StudyObjective_000001",
        )
        if new_selection.objective_uid is not None:
            objective_ar = objective_repo.find_by_uid(
                new_selection.objective_uid, for_update=True
            )
            # if in draft status - approve
            if objective_ar.item_metadata.status == LibraryItemStatus.DRAFT:
                objective_ar.approve(AUTHOR_ID)
                objective_repo.save(objective_ar)
            # if in retired then we return a error
            elif objective_ar.item_metadata.status == LibraryItemStatus.RETIRED:
                raise exceptions.NotFoundException(
                    msg=f"There is no approved Objective with UID '{new_selection.objective_uid}'."
                )
        # add VO to aggregate
        assert selection_aggregate is not None
        selection_aggregate.add_objective_selection(
            new_selection,
            objective_repo.check_exists_final_version,
            self._repos.ct_term_name_repository.term_specific_exists_by_uid,
        )
        selection_aggregate.validate()
        self.study_objective_selection_repository.save(
            selection_aggregate, author_id=AUTHOR_ID
        )

    def reorder_study_objective_with_save(self):
        # Load aggregate
        selection_aggregate = self.study_objective_selection_repository.find_by_study(
            study_uid="Study_000001", for_update=True
        )

        # remove the connection
        assert selection_aggregate is not None
        selection_aggregate.set_new_order_for_selection(
            "StudyObjective_000001", 2, AUTHOR_ID
        )

        # sync with DB and save the update
        self.study_objective_selection_repository.save(selection_aggregate, AUTHOR_ID)
