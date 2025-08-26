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
    inject_and_clear_db("old.json.test.ct.term.attributes.negative")
    db.cypher_query(STARTUP_CT_TERM_ATTRIBUTES_CYPHER)

    yield

    drop_db("old.json.test.ct.term.attributes.negative")


def test_get_all_terms_from_non_existent_codelist(api_client):
    response = api_client.get("/ct/terms/attributes?codelist_uid=non_existent_codelist")

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"] == "CT Codelist with UID 'non_existent_codelist' doesn't exist."
    )


def test_patch_term_attributes_non_draft_term(api_client):
    data = {
        "code_submission_value": "code_submission_value",
        "name_submission_value": "name_submission_value",
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "change_description": "change_description",
    }
    response = api_client.patch("/ct/terms/term_root_final/attributes", json=data)

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_patch_attributes_terms_in_non_editable_library(api_client):
    data = {
        "code_submission_value": "code_submission_value",
        "name_submission_value": "name_submission_value",
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "change_description": "change_description",
    }
    response = api_client.patch(
        "/ct/terms/term_root_draft_non_edit/attributes", json=data
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_patch_attributes_terms_name_submission_value_allready_exists(api_client):
    data = {
        "code_submission_value": "code_submission_value",
        "name_submission_value": "name_submission_value1",
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "change_description": "change_description",
    }
    response = api_client.patch("/ct/terms/term_root_draft/attributes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "CT Term Attributes with Name 'name_submission_value1' already exists."
    )


def test_patch_attributes_terms_code_submission_value_already_exists(api_client):
    data = {
        "code_submission_value": "code_submission_value1",
        "name_submission_value": "name_submission_value",
        "nci_preferred_name": "nci_preferred_name",
        "definition": "definition",
        "change_description": "change_description",
    }
    response = api_client.patch("/ct/terms/term_root_draft/attributes", json=data)

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "CT Term Attributes with Code Submission Value 'code_submission_value1' already exists."
    )


def test_post_attributes_versions_non_editable_library(api_client):
    response = api_client.post("/ct/terms/term_root_draft_non_edit/attributes/versions")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_post_attributes_approve_non_draft_term(api_client):
    response = api_client.post("/ct/terms/term_root_final/attributes/approvals")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "The object isn't in draft status."


def test_post_attributes_approve_non_editable_library(api_client):
    response = api_client.post(
        "/ct/terms/term_root_draft_non_edit/attributes/approvals"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_delete_attributes_activations_non_final_term(api_client):
    response = api_client.delete("/ct/terms/term_root_draft/attributes/activations")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Cannot retire draft version."


def test_delete_attributes_activations_non_editable_library(api_client):
    response = api_client.delete(
        "/ct/terms/term_root_final_non_edit/attributes/activations"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Library isn't editable."


def test_delete_attributes_delete_accepted_term(api_client):
    response = api_client.delete("/ct/terms/term_root_final/attributes")

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert res["message"] == "Object has been accepted"


def test_add_term_node_parent1(api_client):
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


def test_add_term_parent_node_parent_of_the_same_type_already_existing(api_client):
    response = api_client.post(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=type"
    )

    assert_response_status_code(response, 409)

    res = response.json()

    assert res["type"] == "AlreadyExistsException"
    assert (
        res["message"]
        == "Term with UID 'term_root_final' already has a parent type node with UID 'term_root_final' with the relationship of type 'type'"
    )


def test_remove_parent_node_when_the_term_has_no_defined_parent_node_of_given_type(
    api_client,
):
    response = api_client.delete(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=subtype"
    )

    assert_response_status_code(response, 404)

    res = response.json()

    assert res["type"] == "NotFoundException"
    assert (
        res["message"]
        == "Term with UID 'term_root_final' has no defined parent type node with UID 'term_root_final' with the relationship of type 'subtype'"
    )


def test_add_parent_node_wrong_relationship_type_passed(api_client):
    response = api_client.post(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=wrong_type"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "The following type 'wrong_type' isn't valid relationship type."
    )


def test_remove_parent_node_wrong_relationship_type_passed(api_client):
    response = api_client.delete(
        "/ct/terms/term_root_final/parents?parent_uid=term_root_final&relationship_type=wrong_type"
    )

    assert_response_status_code(response, 400)

    res = response.json()

    assert res["type"] == "BusinessLogicException"
    assert (
        res["message"]
        == "The following type 'wrong_type' isn't valid relationship type."
    )
