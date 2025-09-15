# pylint: disable=unused-argument

import dataclasses
import sys
import unittest

import pytest
from neomodel import db

from clinical_mdr_api.domain_repositories.clinical_programmes.clinical_programme_repository import (
    ClinicalProgrammeRepository,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.domain_repositories.projects.project_repository import (
    ProjectRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository import (
    StudyDefinitionRepository,
)
from clinical_mdr_api.domain_repositories.study_definitions.study_definition_repository_impl import (
    StudyDefinitionRepositoryImpl,
)
from clinical_mdr_api.domains.study_definition_aggregates.root import StudyDefinitionAR
from clinical_mdr_api.domains.study_definition_aggregates.study_metadata import (
    StudyDescriptionVO,
)
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import (
    StudyFieldAuditTrailAction,
    StudySoaPreferencesInput,
)
from clinical_mdr_api.tests.integration.domain_repositories._utils import (
    current_function_name,
    wipe_clinical_programme_repository,
    wipe_project_repository,
    wipe_study_definition_repository,
)
from clinical_mdr_api.tests.integration.utils.api import inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_PARAMETERS_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.unit.domain.clinical_programme_aggregate.test_clinical_programme import (
    create_random_clinical_programme,
)
from clinical_mdr_api.tests.unit.domain.project_aggregate.test_project import (
    create_random_project,
)
from clinical_mdr_api.tests.unit.domain.study_definition_aggregate.test_root import (
    create_random_study,
    make_random_study_metadata_edit,
)
from clinical_mdr_api.tests.unit.domain.utils import random_str
from common.auth.user import user
from common.config import settings

IGNORE_ORDER_FOR = [
    "trial_intent_types_codes",
    "trial_phase_codes",
    "trial_type_codes",
    "dictionary_terms",
]
IGNORED_FIELDS = [
    "not_for_update",
    "additional_closure",
    "repository_closure_data",
    "repository",
]


def assert_dataclasses_equal(obj1, obj2):
    for field in dataclasses.fields(obj1):
        attr = field.name
        if attr in IGNORED_FIELDS:
            continue
        attr1 = getattr(obj1, attr)
        attr2 = getattr(obj2, attr)
        if callable(attr1):
            continue
        if attr1 is None:
            assert attr2 is None
        elif isinstance(attr1, list | tuple):
            if attr in IGNORE_ORDER_FOR:
                assert set(attr1) == set(attr2)
            else:
                assert attr1 == attr2
        elif dataclasses.is_dataclass(attr1):
            assert_dataclasses_equal(attr1, attr2)
        else:
            assert attr1 == attr2


class TestStudyDefinitionRepository(unittest.TestCase):
    TEST_DB_NAME = "studydeftest"

    @classmethod
    def setUpClass(cls) -> None:
        inject_and_clear_db(cls.TEST_DB_NAME)
        db.cypher_query(STARTUP_PARAMETERS_CYPHER)

        wipe_study_definition_repository()
        wipe_project_repository()
        wipe_clinical_programme_repository()

        clinical_programme_repo = ClinicalProgrammeRepository()
        cls.created_clinical_programme = create_random_clinical_programme(
            clinical_programme_repo.generate_uid
        )
        clinical_programme_repo.save(cls.created_clinical_programme)

        project_repo = ProjectRepository()
        cls.created_project = create_random_project(
            clinical_programme_uid=cls.created_clinical_programme.uid,
            generate_uid_callback=project_repo.generate_uid,
        )
        project_repo.save(cls.created_project)

        cls.project_to_amend = create_random_project(
            clinical_programme_uid=cls.created_clinical_programme.uid,
            generate_uid_callback=project_repo.generate_uid,
        )
        project_repo.save(cls.project_to_amend)

        TestUtils.create_library()
        TestUtils.create_library(name="UCUM", is_editable=True)
        TestUtils.create_ct_catalogue()
        codelist = TestUtils.create_ct_codelist()
        TestUtils.create_study_ct_data_map(codelist_uid=codelist.codelist_uid)
        TestUtils.create_study_fields_configuration()

    def test__assert_dataclasses_equal(self):
        # create a study
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # edit the study
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository2.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repository2.save(amended_study)
            repository2.close()

        # fetch the edited study and make sure the assert function catches the difference
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository3.find_by_uid(created_study.uid, for_update=False)
            with pytest.raises(AssertionError):
                assert_dataclasses_equal(created_study, amended_study)
            repository3.close()

    def test__find_by_uid__non_existent_uid__returns_none(self):
        with db.transaction:
            # given
            non_existent_uid = f"this-uid-for-sure-does-not-exists-especially-after-adding-this-{random_str()}"
            repository = StudyDefinitionRepositoryImpl(f"{current_function_name()}")

            # when
            result = repository.find_by_uid(non_existent_uid)
            repository.close()

            # then
            self.assertIsNone(result)

    def test__create__exists(self):
        with db.transaction:
            # given
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            # when
            repository1.save(created_study)
            repository1.close()

        # then
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            retrieved_study = repository2.find_by_uid(created_study.uid)
            repository2.close()
        print("CRE", created_study)
        print("RET", retrieved_study)
        assert_dataclasses_equal(retrieved_study, created_study)

    def test__save__locked__locked(self):
        def can_lock(_: StudyDefinitionAR) -> bool:
            return _.current_metadata.id_metadata.study_id is not None

        # given
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                condition=can_lock,
                generate_uid_callback=repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # when
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            study_to_lock = repository2.find_by_uid(created_study.uid, for_update=True)
            study_to_lock.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repository2.save(study_to_lock)
            study_to_lock = repository2.find_by_uid(created_study.uid, for_update=True)
            study_to_lock.lock(
                version_description="locked version",
                author_id=current_function_name(),
            )
            repository2.save(study_to_lock)
            repository2.close()

        # then
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repository3.find_by_uid(created_study.uid)
            repository3.close()
        print("LOCKED", locked_study)
        assert_dataclasses_equal(
            locked_study.current_metadata.ver_metadata,
            study_to_lock.current_metadata.ver_metadata,
        )
        assert_dataclasses_equal(locked_study, study_to_lock)

    def test__save__after_metadata_edit_with_different_values__result(self):
        # given
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # when
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository2.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repository2.save(amended_study)
            repository2.close()

        # then
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repository3.find_by_uid(created_study.uid)
            repository3.close()
        print(f"final {final_retrieved_study}")
        print(f"amended {amended_study}")
        assert_dataclasses_equal(final_retrieved_study, amended_study)

    def test__save__after_metadata_edit_with_same_values__result(self):
        # given
        with db.transaction:
            repository1 = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                repository1.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repository1.save(created_study)
            repository1.close()

        # when
        with db.transaction:
            repository2 = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repository2.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            amended_study.edit_metadata(
                new_id_metadata=amended_study.current_metadata.id_metadata,
                project_exists_callback=lambda _: True,
                author_id=current_function_name(),
            )
            repository2.save(amended_study)
            repository2.close()

        # then
        with db.transaction:
            repository3 = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repository3.find_by_uid(created_study.uid)
            repository3.close()

        assert_dataclasses_equal(final_retrieved_study, amended_study)

    def test__save__after_unlock__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=lambda _: _.study_number is not None,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            amended_study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("LCK", locked_study)
            print("LCK", amended_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                version_description="very important version",
                author_id=current_function_name(),
            )
            repo.save(locked_study)
            repo.close()

        # when
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            unlocked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(unlocked_study, locked_study)
            unlocked_study.unlock(author_id=current_function_name())
            repo.save(unlocked_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, unlocked_study)

    def test__save__after_release__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, amended_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, released_study)

    def test__save__after_release_and_edit__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, amended_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, released_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()
        print(
            "FIN",
            final_retrieved_study.current_metadata.id_metadata.study_number,
            created_study.current_metadata.id_metadata.study_number,
        )
        print(
            "FIN",
            final_retrieved_study.current_metadata.id_metadata.project_number,
            amended_study.current_metadata.id_metadata.project_number,
        )
        print(f"final {final_retrieved_study}")
        print(f"amended {amended_study}")
        assert_dataclasses_equal(final_retrieved_study, amended_study)

    def test__save__after_lock_unlock_release_lock__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=(
                    lambda _: _.project_number is not None
                    and _.study_number is not None
                ),
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            amended_study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                version_description="very important version",
                author_id=current_function_name(),
            )
            repo.save(locked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            unlocked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(unlocked_study, locked_study)
            unlocked_study.unlock(author_id=current_function_name())
            repo.save(unlocked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, unlocked_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, released_study)
            locked_study.lock(
                author_id=current_function_name(),
                version_description="another very important version",
            )
            repo.save(locked_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, locked_study)

    def test__save__after_lock_unlock_release_lock_and_edits_in_between__result(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            created_study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                is_study_after_create=True,
                author_id=current_function_name(),
            )
            repo.save(created_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, created_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=lambda _: _.study_number is not None,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            amended_study.edit_metadata(
                study_title_exists_callback=lambda _, study_number: False,
                study_short_title_exists_callback=lambda _, study_number: False,
                new_study_description=StudyDescriptionVO.from_input_values(
                    study_title="new_study_title", study_short_title="study_short_title"
                ),
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                version_description="very important version",
                author_id=current_function_name(),
            )
            repo.save(locked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            unlocked_study = repo.find_by_uid(created_study.uid, for_update=True)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(unlocked_study, locked_study)
            unlocked_study.unlock(author_id=current_function_name())
            repo.save(unlocked_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("amended_study", amended_study)
            print("unlocked_study", unlocked_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, unlocked_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=(
                    lambda _: _.project_number is not None
                    and _.study_number is not None
                ),
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            released_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("released_study", released_study)
            print("amended_study", amended_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(released_study, amended_study)
            released_study.release(
                change_description="making a release in test",
                author_id=current_function_name(),
            )
            repo.save(released_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            amended_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("amended_study", amended_study)
            print("released_study", released_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(amended_study, released_study)
            make_random_study_metadata_edit(
                amended_study,
                new_id_metadata_condition=lambda _: _.project_number is not None,
                new_id_metadata_fixed_values={
                    "project_number": self.project_to_amend.project_number,
                    "study_number": created_study.current_metadata.id_metadata.study_number,
                },
                author_id=current_function_name(),
            )
            repo.save(amended_study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            locked_study = repo.find_by_uid(created_study.uid, for_update=True)
            print("locked_study", locked_study)
            print("amended_study", amended_study)
            # this is not the test just making sure we are on track here
            assert_dataclasses_equal(locked_study, amended_study)
            locked_study.lock(
                author_id=current_function_name(),
                version_description="another very important version",
            )
            repo.save(locked_study)
            repo.close()

        # then
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            final_retrieved_study = repo.find_by_uid(created_study.uid)
            repo.close()

        assert_dataclasses_equal(final_retrieved_study, locked_study)

    def test__find_all__results(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            test_studies = [
                create_random_study(
                    repo.generate_uid,
                    new_id_metadata_fixed_values={
                        "project_number": self.created_project.project_number
                    },
                    is_study_after_create=True,
                    author_id="test__find_all__results",
                )
                for _ in range(0, 10)
            ]
            for study in test_studies:
                repo.save(study)
            repo.close()

        # when
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            all_studies_in_db = repo.find_all(
                page_number=1, page_size=sys.maxsize
            ).items
            repo.close()

        # then
        # we check if all test_studies are in all_studies_in_db
        # to achieve this we build a dictionary first
        db_studies: dict[str, StudyDefinitionAR] = {}
        for _study in all_studies_in_db:
            db_studies[_study.uid] = _study

        # then we go by test_studies and assert all of them are in the dictionary
        for test_study in test_studies:
            with self.subTest():
                assert_dataclasses_equal(db_studies[test_study.uid], test_study)

    def test__find_all__with_custom_sort_order__success(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            test_studies = [
                create_random_study(
                    repo.generate_uid,
                    new_id_metadata_fixed_values={
                        "project_number": self.created_project.project_number
                    },
                    is_study_after_create=True,
                    author_id="test__find_all__with_custom_sort_order__success",
                )
                for _ in range(0, 10)
            ]
            for study in test_studies:
                repo.save(study)
            repo.close()

        # when
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            all_studies_in_db = repo.find_all(
                page_number=1, page_size=sys.maxsize
            ).items
            repo.close()

        # then
        # we check if all test_studies are in all_studies_in_db
        # to achieve this we build a dictionary first
        # TODO: would be nice to do the sort order check as well (not doing that currently)
        db_studies: dict[str, StudyDefinitionAR] = {}
        for _study in all_studies_in_db:
            db_studies[_study.uid] = _study

        # then we go by test_studies and assert all of them are in the dictionary
        for test_study in test_studies:
            with self.subTest():
                assert_dataclasses_equal(db_studies[test_study.uid], test_study)

    def test__find_by_id__find_for_update_without_transaction__failure(self):
        # given
        uid = "some-uid"

        # then
        with self.assertRaises(SystemError):
            # when
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            repo.find_by_uid(uid, for_update=True)

    def test__save__after_create_and_closing_transaction__failure(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )

        # then
        with self.assertRaises(SystemError):
            # when
            repo.save(study)

    def test__save__after_retrieve_for_update_and_closing_transaction__failure(self):
        # given
        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            study = create_random_study(
                generate_uid_callback=repo.generate_uid,
                new_id_metadata_fixed_values={
                    "project_number": self.created_project.project_number
                },
                author_id=current_function_name(),
            )
            repo.save(study)
            repo.close()

        with db.transaction:
            repo = StudyDefinitionRepositoryImpl(current_function_name())
            study = repo.find_by_uid(study.uid, for_update=True)

        # then
        with self.assertRaises(SystemError):
            # when
            repo.save(study)


@pytest.mark.parametrize(
    ("soa_preferences_input", "expected_preferences"),
    (
        (  # 0
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 1
            StudySoaPreferencesInput(show_milestones=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 2
            StudySoaPreferencesInput(
                show_milestones=True, show_epochs=False, baseline_as_time_zero=True
            ),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 3
            StudySoaPreferencesInput(show_epochs=True, baseline_as_time_zero=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 4
            StudySoaPreferencesInput(
                show_epochs=False, show_milestones=False, baseline_as_time_zero=False
            ),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 5
            StudySoaPreferencesInput(show_milestones=True, show_epochs=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 6
            StudySoaPreferencesInput(show_epochs=True, show_milestones=False),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
        ),
        (  # 7
            StudySoaPreferencesInput(
                baseline_as_time_zero=True, show_epochs=True, show_milestones=False
            ),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
        (  # 8
            StudySoaPreferencesInput(baseline_as_time_zero=True),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
            },
        ),
    ),
)
def test_post_soa_preferences(
    base_data,
    tst_project: Project,
    soa_preferences_input: StudySoaPreferencesInput,
    expected_preferences: dict[str, bool],
):
    repo: StudyDefinitionRepository = StudyDefinitionRepositoryImpl(user().id())

    study = TestUtils.create_study(project_number=tst_project.project_number)

    # should have two StudySoaPreferencesInput created at Study creation
    nodes = repo.get_soa_preferences(study.uid)
    assert len(nodes) == 3

    unlink_study_soa_properties(study.uid, repo)

    assert not repo.get_soa_preferences(study.uid)

    with db.transaction:
        nodes = repo.post_soa_preferences(study.uid, soa_preferences_input)

    preferences = {node.field_name: node.value for node in nodes}
    assert preferences == expected_preferences


@pytest.mark.parametrize(
    (
        "soa_preferences_initial",
        "soa_preferences_update",
        "expected_preferences",
        "expected_num_actions",
    ),
    (
        (None, StudySoaPreferencesInput(), {}, 3),  # 0
        (  # 1
            StudySoaPreferencesInput(show_epochs=False, show_milestones=True),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
            },
            6,
        ),
        (  # 2
            StudySoaPreferencesInput(
                show_epochs=False, show_milestones=False, baseline_as_time_zero=False
            ),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            6,
        ),
        (  # 3
            StudySoaPreferencesInput(
                show_epochs=True, show_milestones=False, baseline_as_time_zero=True
            ),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
            },
            6,
        ),
        (  # 4
            StudySoaPreferencesInput(
                show_epochs=True, show_milestones=True, baseline_as_time_zero=True
            ),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": True,
                "baseline_as_time_zero": True,
            },
            6,
        ),
        (  # 5
            StudySoaPreferencesInput(),
            StudySoaPreferencesInput(),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            6,
        ),
        (  # 6
            StudySoaPreferencesInput(show_milestones=False),
            StudySoaPreferencesInput(show_milestones=False),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            6,
        ),
        (  # 7
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": False,
            },
            6,
        ),
        (  # 8
            StudySoaPreferencesInput(show_epochs=True),
            StudySoaPreferencesInput(show_milestones=False, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            7,
        ),
        (  # 9
            StudySoaPreferencesInput(show_epochs=True),
            StudySoaPreferencesInput(show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            7,
        ),
        (  # 10
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            StudySoaPreferencesInput(show_epochs=True, show_milestones=False),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            8,
        ),
        (  # 11
            StudySoaPreferencesInput(
                show_milestones=True, show_epochs=False, baseline_as_time_zero=True
            ),
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": True,
                "baseline_as_time_zero": True,
            },
            6,
        ),
        (  # 12
            StudySoaPreferencesInput(show_epochs=True, baseline_as_time_zero=False),
            StudySoaPreferencesInput(show_milestones=False, show_epochs=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            7,
        ),
        (  # 13
            StudySoaPreferencesInput(show_epochs=True, baseline_as_time_zero=True),
            StudySoaPreferencesInput(show_epochs=False, baseline_as_time_zero=False),
            {
                "soa_show_epochs": False,
                "soa_show_milestones": False,
                "baseline_as_time_zero": False,
            },
            8,
        ),
        (  # 14
            StudySoaPreferencesInput(show_milestones=True, show_epochs=False),
            StudySoaPreferencesInput(
                show_epochs=True, show_milestones=False, baseline_as_time_zero=True
            ),
            {
                "soa_show_epochs": True,
                "soa_show_milestones": False,
                "baseline_as_time_zero": True,
            },
            9,
        ),
    ),
)
def test_edit_soa_preferences(
    base_data,
    tst_project: Project,
    soa_preferences_initial: StudySoaPreferencesInput | None,
    soa_preferences_update: StudySoaPreferencesInput,
    expected_preferences: dict[str, bool],
    expected_num_actions: int,
):
    repo: StudyDefinitionRepository = StudyDefinitionRepositoryImpl(user().id())

    study = TestUtils.create_study(project_number=tst_project.project_number)

    unlink_study_soa_properties(study.uid, repo)

    if soa_preferences_initial:
        with db.transaction:
            repo.post_soa_preferences(study.uid, soa_preferences_initial)

    with db.transaction:
        nodes = repo.edit_soa_preferences(study.uid, soa_preferences_update)

    preferences = {node.field_name: node.value for node in nodes}
    assert preferences == expected_preferences

    actions = _get_study_soa_preferences_audit_trail_actions(study.uid, repo)
    assert len(actions) == expected_num_actions

    for action in actions:
        if action.action == "Create":
            assert action.before_value is None
        if action.action == "Edit":
            assert action.before_value is not None
        assert action.after_value is not None


def _get_study_soa_preferences_audit_trail_actions(
    study_uid: str, repo: StudyDefinitionRepository
) -> list[StudyFieldAuditTrailAction]:
    """Gets audit trail actions on StudySoaPreferences fields"""

    trails = repo.get_audit_trail_by_uid(study_uid)
    trails.sort(key=lambda x: x.date)

    actions = [
        action
        for trail in trails
        for action in trail.actions
        if action.field_name in settings.study_soa_preferences_fields
    ]

    return actions


def unlink_study_soa_properties(
    study_uid: str, repo: StudyDefinitionRepository | None = None
):
    """Removes existing StudySoaPreferences"""

    if repo is None:
        repo = StudyDefinitionRepositoryImpl(user().id())

    latest_study_value = StudyRoot.nodes.get(uid=study_uid).latest_value.single()

    for node in repo.get_soa_preferences(study_uid):
        latest_study_value.has_boolean_field.disconnect(node)
