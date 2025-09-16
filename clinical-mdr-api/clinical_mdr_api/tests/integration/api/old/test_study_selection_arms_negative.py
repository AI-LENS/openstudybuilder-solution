# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_NAME_CYPHER,
    STARTUP_STUDY_ARM_CYPHER,
)
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.study.selection.arms.negative")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)
    db.cypher_query(STARTUP_STUDY_ARM_CYPHER)
    TestUtils.set_study_standard_version(
        study_uid="study_root", create_codelists_and_terms_for_package=False
    )

    # locking and unlocking to create multiple study value relationships on the existent StudySelections
    TestUtils.create_study_fields_configuration()

    yield

    drop_db("old.json.test.study.selection.arms.negative")


def test_adding_selection2(api_client):
    data = {
        "name": "Arm_Name_1",
        "short_name": "Arm_Short_Name_1",
        "code": "Arm_code_1",
        "description": "desc...",
        "randomization_group": "Randomization_Group_1",
        "number_of_subjects": 1,
        "arm_type_uid": "term_root_final",
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000001"
    assert res["order"] == 1
    assert res["name"] == "Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_1"
    assert res["code"] == "Arm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_2nd_selection(api_client):
    data = {
        "name": "Arm_Name_2",
        "short_name": "Arm_Short_Name_2",
        "code": "Arm_code_2",
        "description": "desc...",
        "randomization_group": "Randomization_Group_2",
        "number_of_subjects": 1,
        "arm_type_uid": "term_root_final",
    }
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000002"
    assert res["order"] == 2
    assert res["name"] == "Arm_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["author_username"] == "unknown-user@example.com"


def test_adding_selection_with_non_unique_name_short_name_randomization(api_client):
    data = {"name": "Arm_Name_1"}
    response = api_client.post("/studies/study_root/study-arms", json=data)

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Arm_Name_1' in field Arm name is not unique for the study."
    )


def test_patch_specific_set_name2(api_client):
    data = {
        "name": "New_Arm_Name_1",
        "short_name": "Arm_Short_Name_1",
        "arm_type_uid": "term_root_final_non_edit",
    }
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000001", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["arm_uid"] == "StudyArm_000001"
    assert res["order"] == 1
    assert res["name"] == "New_Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_1"
    assert res["code"] == "Arm_code_1"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 3
    assert res["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "CDISC"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["arm_connected_branch_arms"] is None
    assert res["description"] == "desc..."
    assert res["number_of_subjects"] == 1
    assert res["randomization_group"] == "Randomization_Group_1"
    assert res["author_username"] == "unknown-user@example.com"


def test_all_history_of_specific_selection2(api_client):
    response = api_client.get(
        "/studies/study_root/study-arms/StudyArm_000001/audit-trail/"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res[0]["study_uid"] == "study_root"
    assert res[0]["order"] == 1
    assert res[0]["arm_uid"] == "StudyArm_000001"
    assert res[0]["name"] == "New_Arm_Name_1"
    assert res[0]["short_name"] == "Arm_Short_Name_1"
    assert res[0]["code"] == "Arm_code_1"
    assert res[0]["description"] == "desc..."
    assert res[0]["randomization_group"] == "Randomization_Group_1"
    assert res[0]["number_of_subjects"] == 1
    assert res[0]["arm_type"]["term_uid"] == "term_root_final_non_edit"
    assert res[0]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[0]["arm_type"]["codelists"]) == 1
    assert res[0]["arm_type"]["codelists"][0]["codelist_uid"] == "non_editable_cr"
    assert res[0]["arm_type"]["codelists"][0]["order"] == 3
    assert res[0]["arm_type"]["codelists"][0]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["sponsor_preferred_name"] == "term_value_name3"
    assert (
        res[0]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[0]["arm_type"]["library_name"] == "CDISC"
    assert res[0]["arm_type"]["start_date"]
    assert res[0]["arm_type"]["end_date"] is None
    assert res[0]["arm_type"]["status"] == "Final"
    assert res[0]["arm_type"]["version"] == "1.0"
    assert res[0]["arm_type"]["change_description"] == "Approved version"
    assert res[0]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[0]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[0]["author_username"] == "unknown-user@example.com"
    assert res[0]["end_date"] is None
    assert res[0]["status"] is None
    assert res[0]["change_type"] == "Edit"
    assert res[0]["accepted_version"] is False
    assert res[1]["study_uid"] == "study_root"
    assert res[1]["order"] == 1
    assert res[1]["arm_uid"] == "StudyArm_000001"
    assert res[1]["name"] == "Arm_Name_1"
    assert res[1]["short_name"] == "Arm_Short_Name_1"
    assert res[1]["code"] == "Arm_code_1"
    assert res[1]["description"] == "desc..."
    assert res[1]["randomization_group"] == "Randomization_Group_1"
    assert res[1]["number_of_subjects"] == 1
    assert res[1]["arm_type"]["term_uid"] == "term_root_final"
    assert res[1]["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res[1]["arm_type"]["codelists"]) == 1
    assert res[1]["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res[1]["arm_type"]["codelists"][0]["order"] == 1
    assert res[1]["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res[1]["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res[1]["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res[1]["arm_type"]["library_name"] == "Sponsor"
    assert res[1]["arm_type"]["start_date"]
    assert res[1]["arm_type"]["end_date"] is None
    assert res[1]["arm_type"]["status"] == "Final"
    assert res[1]["arm_type"]["version"] == "1.0"
    assert res[1]["arm_type"]["change_description"] == "Approved version"
    assert res[1]["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res[1]["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res[1]["author_username"] == "unknown-user@example.com"
    assert res[1]["end_date"]
    assert res[1]["status"] is None
    assert res[1]["change_type"] == "Create"
    assert res[1]["accepted_version"] is False


def test_patch_specific_patch_a_randomization_group_name_that_is_in_history_not_latest(
    api_client,
):
    data = {"name": "Arm_Name_1"}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000002", json=data
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["study_uid"] == "study_root"
    assert res["order"] == 2
    assert res["arm_uid"] == "StudyArm_000002"
    assert res["name"] == "Arm_Name_1"
    assert res["short_name"] == "Arm_Short_Name_2"
    assert res["code"] == "Arm_code_2"
    assert res["description"] == "desc..."
    assert res["randomization_group"] == "Randomization_Group_2"
    assert res["number_of_subjects"] == 1
    assert res["arm_type"]["term_uid"] == "term_root_final"
    assert res["arm_type"]["catalogue_name"] == "SDTM CT"
    assert len(res["arm_type"]["codelists"]) == 1
    assert res["arm_type"]["codelists"][0]["codelist_uid"] == "editable_cr"
    assert res["arm_type"]["codelists"][0]["order"] == 1
    assert res["arm_type"]["codelists"][0]["library_name"] == "Sponsor"
    assert res["arm_type"]["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["arm_type"]["sponsor_preferred_name_sentence_case"]
        == "term_value_name_sentence_case"
    )
    assert res["arm_type"]["library_name"] == "Sponsor"
    assert res["arm_type"]["start_date"]
    assert res["arm_type"]["end_date"] is None
    assert res["arm_type"]["status"] == "Final"
    assert res["arm_type"]["version"] == "1.0"
    assert res["arm_type"]["change_description"] == "Approved version"
    assert res["arm_type"]["author_username"] == "unknown-user@example.com"
    assert res["arm_type"]["possible_actions"] == ["inactivate", "new_version"]
    assert res["author_username"] == "unknown-user@example.com"
    assert res["end_date"] is None
    assert res["status"] is None
    assert res["change_type"] is None
    assert res["accepted_version"] is False
    assert res["arm_connected_branch_arms"] is None


def test_patch_specific_patch_some_randomization_group_that_is_already_used_on_another_branch(
    api_client,
):
    data = {"randomization_group": "Randomization_Group_2"}
    response = api_client.patch(
        "/studies/study_root/study-arms/StudyArm_000001", json=data
    )

    assert_response_status_code(response, 422)

    res = response.json()

    assert res["type"] == "ValidationException"
    assert (
        res["message"]
        == "Value 'Randomization_Group_2' in field Arm Randomization code is not unique for the study."
    )
