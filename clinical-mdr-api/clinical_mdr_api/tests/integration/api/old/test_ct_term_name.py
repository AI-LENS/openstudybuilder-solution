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
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.term.name")
    db.cypher_query(STARTUP_CT_TERM_NAME_CYPHER)

    yield

    drop_db("old.json.test.ct.term.name")


def test_reorder_term(api_client):
    data = {"codelist_uid": "editable_cr", "new_order": 5}
    response = api_client.patch("/ct/terms/term_root_draft/order", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 5, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_value"
    assert res["name_submission_value"] == "name_submission_value"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name2"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_patch_term_names_draft_term(api_client):
    data = {
        "sponsor_preferred_name": "Sponsor_Preferred_Name",
        "sponsor_preferred_name_sentence_case": "sponsor_preferred_name",
        "change_description": "Term name update",
    }
    response = api_client.patch("/ct/terms/term_root_draft/names", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 5, "library_name": "Sponsor"}
    ]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Term name update"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_names_approve_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/names/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 5, "library_name": "Sponsor"}
    ]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Approved version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_names_activations_term(api_client):
    response = api_client.delete("/ct/terms/term_root_draft/names/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 5, "library_name": "Sponsor"}
    ]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Inactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["reactivate"]


def test_post_names_reactivate_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/names/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 5, "library_name": "Sponsor"}
    ]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "Reactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_post_names_versions(api_client):
    response = api_client.post("/ct/terms/term_root_draft/names/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 5, "library_name": "Sponsor"}
    ]
    assert res["sponsor_preferred_name"] == "Sponsor_Preferred_Name"
    assert res["sponsor_preferred_name_sentence_case"] == "sponsor_preferred_name"
    assert res["change_description"] == "New draft created"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["queried_effective_date"] is None
    assert res["date_conflict"] is False
    assert res["possible_actions"] == ["approve", "edit"]
