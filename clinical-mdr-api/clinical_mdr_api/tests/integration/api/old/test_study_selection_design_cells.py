# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.domain_repositories.models.study import StudyRoot
from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_CATALOGUE_CYPHER,
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
    STARTUP_STUDY_BRANCH_ARM_CYPHER,
    STARTUP_STUDY_LIST_CYPHER,
    fix_study_preferred_time_unit,
)
from clinical_mdr_api.tests.integration.utils.method_library import (
    create_codelist,
    create_ct_term,
    create_study_element,
    create_study_epoch,
    create_study_epoch_codelists_ret_cat_and_lib,
    get_catalogue_name_library_name,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code
from common.config import settings


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.design.cells")
    db.cypher_query(STARTUP_STUDY_LIST_CYPHER)
    db.cypher_query(STARTUP_CT_CATALOGUE_CYPHER)

    StudyRoot.generate_node_uids_if_not_present()
    study = StudyRoot.nodes.all()[0]
    TestUtils.create_ct_catalogue(catalogue_name=settings.sdtm_ct_catalogue_name)
    TestUtils.set_study_standard_version(
        study_uid=study.uid, create_codelists_and_terms_for_package=False
    )

    create_study_epoch_codelists_ret_cat_and_lib()
    catalogue_name, library_name = get_catalogue_name_library_name()
    create_study_epoch("EpochSubType_0001")

    element_type_codelist = create_codelist(
        "Element Type", "CTCodelist_ElementType", catalogue_name, library_name
    )
    element_type_term = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0001",
        1,
        catalogue_name,
        library_name,
    )
    element_type_term_2 = create_ct_term(
        element_type_codelist.codelist_uid,
        "Element Type",
        "ElementType_0002",
        2,
        catalogue_name,
        library_name,
    )
    create_study_element(element_type_term.uid, study.uid)
    create_study_element(element_type_term_2.uid, study.uid)

    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    db.cypher_query(STARTUP_STUDY_BRANCH_ARM_CYPHER)
    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.create_study_fields_configuration()

    fix_study_preferred_time_unit(study.uid)

    yield

    drop_db("old.json.test.study.selection.design.cells")


def test_adding_selection_1st1(api_client):
    data = {
        "name": "BranchArm_Name_1",
        "short_name": "BranchArm_Short_Name_1",
        "code": "BranchArm_code_1",
        "description": "desc...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000001"
    assert res["order"] == 1
    assert res["name"] == "BranchArm_Name_1"
    assert res["short_name"] == "BranchArm_Short_Name_1"
    assert res["code"] == "BranchArm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_2nd1(api_client):
    data = {
        "name": "BranchArm_Name_2",
        "short_name": "BranchArm_Short_Name_2",
        "code": "BranchArm_code_2",
        "description": "desc...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000002"
    assert res["order"] == 2
    assert res["name"] == "BranchArm_Name_2"
    assert res["short_name"] == "BranchArm_Short_Name_2"
    assert res["code"] == "BranchArm_code_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_3rd(api_client):
    data = {
        "name": "BranchArm_Name_3",
        "short_name": "BranchArm_Short_Name_3",
        "code": "BranchArm_code_3",
        "description": "desc...",
        "randomization_group": "Randomization_Group_3",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000003"
    assert res["order"] == 3
    assert res["name"] == "BranchArm_Name_3"
    assert res["short_name"] == "BranchArm_Short_Name_3"
    assert res["code"] == "BranchArm_code_3"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_3"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_4th(api_client):
    data = {
        "name": "BranchArm_Name_4",
        "short_name": "BranchArm_Short_Name_4",
        "code": "BranchArm_code_4",
        "description": "desc...",
        "randomization_group": "Randomization_Group_4",
        "number_of_subjects": 2,
        "arm_uid": "StudyArm_000001",
    }
    response = api_client.post("/studies/study_root/study-branch-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["study_version"]
    assert res["branch_arm_uid"] == "StudyBranchArm_000004"
    assert res["order"] == 4
    assert res["name"] == "BranchArm_Name_4"
    assert res["short_name"] == "BranchArm_Short_Name_4"
    assert res["code"] == "BranchArm_code_4"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_root"]["study_uid"] == "study_root"
    assert res["arm_root"]["arm_uid"] == "StudyArm_000001"
    assert res["arm_root"]["order"] == 1
    assert res["arm_root"]["name"] == "StudyArm_000001"
    assert res["arm_root"]["short_name"] == "StudyArm_000001"
    assert res["arm_root"]["code"] is None
    assert res["arm_root"]["start_date"]
    assert res["arm_root"]["end_date"] is None
    assert res["arm_root"]["status"] is None
    assert res["arm_root"]["change_type"] is None
    assert res["arm_root"]["accepted_version"] is None
    assert res["arm_root"]["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_root"]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_root"]["arm_type"]["codelists"]) == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_root"]["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_root"]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_root"]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_root"]["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_root"]["arm_type"]["start_date"]
    assert res["arm_root"]["arm_type"]["end_date"] is None
    assert res["arm_root"]["arm_type"]["status"] == "Final"
    assert res["arm_root"]["arm_type"]["version"] == "1.0"
    assert res["arm_root"]["arm_type"]["change_description"] == "Approved version"
    assert res["arm_root"]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_root"]["arm_type"]["queried_effective_date"]
    assert res["arm_root"]["arm_type"]["date_conflict"] is False
    assert res["arm_root"]["arm_type"]["possible_actions"] == [
        "inactivate",
        "new_version",
    ]
    assert res["arm_root"]["description"] is None
    assert res["arm_root"]["number_of_subjects"] is None
    assert res["arm_root"]["randomization_group"] is None
    assert res["arm_root"]["author_username"] == "unknown-user@example.com"
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 2
    assert res["randomization_group"] == "Randomization_Group_4"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_1st_studydesigncell(api_client):
    data = {
        "study_branch_arm_uid": "StudyBranchArm_000002",
        "study_epoch_uid": "StudyEpoch_000001",
        "study_element_uid": "StudyElement_000001",
        "transition_rule": "Transition_Rule_1",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_add_study_title_test_to_have_multiple_study_value_relationships_attached4(
    api_client,
):
    data = {"current_metadata": {"study_description": {"study_title": "new title"}}}
    response = api_client.patch("/studies/study_root", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["uid"] == "study_root"
    assert res["possible_actions"] == ["delete", "lock", "release"]
    assert res["study_parent_part"] is None
    assert res["study_subpart_uids"] == []
    assert res["current_metadata"]["identification_metadata"]["study_number"] == "0"
    assert res["current_metadata"]["identification_metadata"]["subpart_id"] is None
    assert res["current_metadata"]["identification_metadata"]["study_acronym"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["study_subpart_acronym"]
        is None
    )
    assert res["current_metadata"]["identification_metadata"]["project_number"] == "123"
    assert res["current_metadata"]["identification_metadata"]["description"] is None
    assert (
        res["current_metadata"]["identification_metadata"]["project_name"]
        == "Project ABC"
    )
    assert (
        res["current_metadata"]["identification_metadata"]["clinical_programme_name"]
        == "CP"
    )
    assert res["current_metadata"]["identification_metadata"]["study_id"] == "some_id-0"
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "ct_gov_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudract_id_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "universal_trial_number_utn_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_id_japic_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_new_drug_application_number_ind_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eu_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "civ_id_sin_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_clinical_trial_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "japanese_trial_registry_number_jrct_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "national_medical_products_administration_nmpa_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "eudamed_srn_number_null_value_code"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number"
        ]
        is None
    )
    assert (
        res["current_metadata"]["identification_metadata"]["registry_identifiers"][
            "investigational_device_exemption_ide_number_null_value_code"
        ]
        is None
    )
    assert res["current_metadata"]["version_metadata"]["study_status"] == "DRAFT"
    assert res["current_metadata"]["version_metadata"]["version_number"] is None
    assert res["current_metadata"]["version_metadata"]["version_timestamp"]
    assert (
        res["current_metadata"]["version_metadata"]["version_author"]
        == "unknown-user@example.com"
    )
    assert res["current_metadata"]["version_metadata"]["version_description"] is None
    assert res["current_metadata"]["study_description"] == {
        "study_title": "new title",
        "study_short_title": None,
    }


def test_lock_study_test_to_have_multiple_study_value_relationships_attached9(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached9(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_adding_studydesigncell_selection_2nd(api_client):
    data = {
        "study_arm_uid": "StudyArm_000002",
        "study_epoch_uid": "StudyEpoch_000001",
        "study_element_uid": "StudyElement_000003",
        "transition_rule": "Transition_Rule_2",
    }
    response = api_client.post("/studies/study_root/study-design-cells", json=data)

    assert_response_status_code(response, 201)


def test_batch_patch_studydesigncell_selection(api_client):
    data = [
        {
            "method": "PATCH",
            "content": {
                "study_design_cell_uid": "StudyDesignCell_000002",
                "study_branch_arm_uid": "StudyBranchArm_000004",
                "study_element_uid": "StudyElement_000001",
            },
        },
        {
            "method": "PATCH",
            "content": {
                "study_design_cell_uid": "StudyDesignCell_000001",
                "study_arm_uid": "StudyArm_000002",
                "study_element_uid": "StudyElement_000003",
                "study_branch_arm_uid": None,
            },
        },
    ]
    response = api_client.post(
        "/studies/study_root/study-design-cells/batch", json=data
    )

    assert_response_status_code(response, 207)


def test_get_all_within_an_arm_list_non_empty1(api_client):
    response = api_client.get(
        "/studies/study_root/study-design-cells/arm/StudyArm_000002"
    )

    assert_response_status_code(response, 200)


def test_get_all_within_a_branch_arm_list_non_empty(api_client):
    response = api_client.get(
        "/studies/study_root/study-design-cells/branch-arm/StudyBranchArm_000004"
    )

    assert_response_status_code(response, 200)


def test_get_all_within_an_epoch_non_empty(api_client):
    response = api_client.get(
        "/studies/study_root/study-design-cells/study-epochs/StudyEpoch_000001"
    )

    assert_response_status_code(response, 200)


def test_get_audit_trail_for_an_specific_design_cell(api_client):
    response = api_client.get(
        "/studies/study_root/study-design-cells/StudyDesignCell_000002/audit-trail/"
    )

    assert_response_status_code(response, 200)


def test_get_audit_trail_for_all_design_cells(api_client):
    response = api_client.get("/studies/study_root/study-design-cells/audit-trail/")

    assert_response_status_code(response, 200)


def test_lock_study_test_to_have_multiple_study_value_relationships_attached10(
    api_client,
):
    data = {"change_description": "Lock 1"}
    response = api_client.post("/studies/study_root/locks", json=data)

    assert_response_status_code(response, 201)


def test_unlock_study_test_to_have_multiple_study_value_relationships_attached10(
    api_client,
):
    response = api_client.delete("/studies/study_root/locks")

    assert_response_status_code(response, 200)


def test_batch_delete_selection(api_client):
    data = [
        {"method": "DELETE", "content": {"uid": "StudyDesignCell_000001"}},
        {"method": "DELETE", "content": {"uid": "StudyDesignCell_000002"}},
    ]
    response = api_client.post(
        "/studies/study_root/study-design-cells/batch", json=data
    )

    assert_response_status_code(response, 207)
