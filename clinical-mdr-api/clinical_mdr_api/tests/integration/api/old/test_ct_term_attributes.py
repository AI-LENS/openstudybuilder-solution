# pylint: disable=unused-argument, redefined-outer-name, too-many-arguments, line-too-long, too-many-statements

# pytest fixture functions have other fixture functions as arguments,
# which pylint interprets as unused arguments

import pytest
from fastapi.testclient import TestClient
from neomodel import db

from clinical_mdr_api.main import app
from clinical_mdr_api.tests.integration.utils.api import drop_db, inject_and_clear_db
from clinical_mdr_api.tests.integration.utils.data_library import (
    STARTUP_CT_TERM_ATTRIBUTES_CYPHER,
)
from clinical_mdr_api.tests.utils.checks import assert_response_status_code


@pytest.fixture(scope="module")
def api_client(test_data):
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data():
    inject_and_clear_db("old.json.test.ct.term.attributes")
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)

    yield

    drop_db("old.json.test.ct.term.attributes")


def test_post_create_term(api_client):
    data = {
        "catalogue_name": "SDTM CT",
        "codelist_uid": "editable_cr",
        "code_submission_value": "code_submission_value",
        "name_submission_value": "name_submission_value",
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "sponsor_preferred_name": "string",
        "sponsor_preferred_name_sentence_case": "string",
        "order": 7,
        "library_name": "Sponsor",
    }
    response = api_client.post("/ct/terms", json=data)

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "CTTerm_000001"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 7, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_value"
    assert res["name_submission_value"] == "name_submission_value"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "string"
    assert res["sponsor_preferred_name_sentence_case"] == "string"
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_patch_term_attributes_draft_term(api_client):
    data = {
        "code_submission_value": "code_submission_valuePATCHED",
        "name_submission_value": "name_submission_valuePATCHED",
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "change_description": "change_description",
    }
    response = api_client.patch("/ct/terms/term_root_draft/attributes", json=data)

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 2, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_valuePATCHED"
    assert res["name_submission_value"] == "name_submission_valuePATCHED"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["change_description"] == "change_description"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "0.2"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "delete", "edit"]


def test_post_attributes_approve_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/attributes/approvals")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 2, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_valuePATCHED"
    assert res["name_submission_value"] == "name_submission_valuePATCHED"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["change_description"] == "Approved version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_delete_attributes_activations_term(api_client):
    response = api_client.delete("/ct/terms/term_root_draft/attributes/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 2, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_valuePATCHED"
    assert res["name_submission_value"] == "name_submission_valuePATCHED"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["change_description"] == "Inactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Retired"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["reactivate"]


def test_post_attributes_reactivate_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/attributes/activations")

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 2, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_valuePATCHED"
    assert res["name_submission_value"] == "name_submission_valuePATCHED"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["change_description"] == "Reactivated version"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Final"
    assert res["version"] == "1.0"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_post_attributes_versions_term(api_client):
    response = api_client.post("/ct/terms/term_root_draft/attributes/versions")

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_draft"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 2, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_valuePATCHED"
    assert res["name_submission_value"] == "name_submission_valuePATCHED"
    assert res["nci_preferred_name"] == "nci_preferred_name"
    assert res["definition"] == "definition"
    assert res["change_description"] == "New draft created"
    assert res["library_name"] == "Sponsor"
    assert res["end_date"] is None
    assert res["status"] == "Draft"
    assert res["version"] == "1.1"
    assert res["author_username"] == "unknown-user@example.com"
    assert res["possible_actions"] == ["approve", "edit"]


def test_add_term_node_parent(api_client):
    response = api_client.post(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_final"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 1, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_value1"
    assert res["name_submission_value"] == "name_submission_value1"
    assert res["nci_preferred_name"] == "preferred_term1"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_remove_term_node_parent(api_client):
    response = api_client.delete(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 200)

    res = response.json()

    assert res["term_uid"] == "term_root_final"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 1, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_value1"
    assert res["name_submission_value"] == "name_submission_value1"
    assert res["nci_preferred_name"] == "preferred_term1"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]


def test_add_term_node_parent_after_deleting(api_client):
    response = api_client.post(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 201)

    res = response.json()

    assert res["term_uid"] == "term_root_final"
    assert res["catalogue_name"] == "SDTM CT"
    assert res["codelists"] == [
        {"codelist_uid": "editable_cr", "order": 1, "library_name": "Sponsor"}
    ]
    assert res["concept_id"] is None
    assert res["code_submission_value"] == "code_submission_value1"
    assert res["name_submission_value"] == "name_submission_value1"
    assert res["nci_preferred_name"] == "preferred_term1"
    assert res["definition"] == "definition"
    assert res["sponsor_preferred_name"] == "term_value_name1"
    assert (
        res["sponsor_preferred_name_sentence_case"] == "term_value_name_sentence_case"
    )
    assert res["library_name"] == "Sponsor"
    assert res["possible_actions"] == ["inactivate", "new_version"]
