# pylint: disable=unused-argument
# pylint: disable=redefined-outer-name
# pylint: disable=too-many-arguments
from typing import Any

import pytest
from fastapi.testclient import TestClient

from clinical_mdr_api.tests.integration.utils.api import inject_base_data
from clinical_mdr_api.tests.integration.utils.utils import TestUtils
from common.config import settings
from consumer_api.consumer_api import app
from consumer_api.tests.utils import assert_response_status_code, set_db
from consumer_api.v1 import models

BASE_URL = "/v1"


LIBRARY_ACTIVITY_FIELDS_ALL = [
    "uid",
    "name",
    "groupings",
    "library",
    "definition",
    "nci_concept_id",
    "nci_concept_name",
    "is_data_collected",
    "status",
    "version",
]

LIBRARY_ACTIVITY_FIELDS_NOT_NULL = [
    "uid",
    "library",
    "status",
    "version",
    "name",
    "groupings",
    "is_data_collected",
]

LIBRARY_ACTIVITY_INSTANCE_FIELDS_ALL = [
    "uid",
    "name",
    "groupings",
    "library",
    "definition",
    "nci_concept_id",
    "nci_concept_name",
    "topic_code",
    "param_code",
    "status",
    "version",
]

LIBRARY_ACTIVITY_INSTANCE_FIELDS_NOT_NULL = [
    "uid",
    "name",
    "groupings",
    "library",
    "topic_code",
    "param_code",
    "status",
    "version",
]


# Global variables shared between fixtures and tests
activities: list[models.LibraryActivity]
total_activities: int = 25
activity_group: Any
activity_subgroup: Any
activity_instances: list[models.LibraryActivityInstance]


@pytest.fixture(scope="module")
def api_client(test_data):
    """Create FastAPI test client
    using the database name set in the `test_data` fixture"""
    yield TestClient(app)


@pytest.fixture(scope="module")
def test_data(api_client):
    """Initialize test data"""
    db_name = "consumer-api-v1-library"
    set_db(db_name)
    inject_base_data()
    global activities
    global activity_group
    global activity_subgroup
    global activity_instances

    activity_instance_class = TestUtils.create_activity_instance_class(
        name="Randomized activity instance class"
    )

    activities = []
    activity_instances = []

    activity_group = TestUtils.create_activity_group("Activity Group")
    activity_subgroup = TestUtils.create_activity_subgroup(
        "Activity Sub Group", activity_groups=[activity_group.uid]
    )

    for idx in range(0, total_activities):
        # Create Final Activity
        activity = TestUtils.create_activity(
            f"Activity {str(idx + 1).zfill(2)}",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
            approve=True,
        )
        activities.append(activity)

        activity_instance = TestUtils.create_activity_instance(
            name=f"Activity instance {idx} - Final",
            activity_instance_class_uid=activity_instance_class.uid,
            name_sentence_case=f"activity instance {idx} - final",
            topic_code=f"TC {idx} final",
            adam_param_code=f"randomized adam_param_code {idx} final",
            is_required_for_activity=True,
            activities=[activity.uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[],
            approve=True,
        )
        activity_instances.append(activity_instance)

        # Create Draft Activity Instance
        # (This is to ensure that we have both Final and Draft activities)
        activity_instance = TestUtils.create_activity_instance(
            name=f"Activity instance {idx} - Draft",
            activity_instance_class_uid=activity_instance_class.uid,
            name_sentence_case=f"activity instance {idx} - draft",
            topic_code=f"TC {idx} draft",
            adam_param_code=f"randomized adam_param_code {idx} draft",
            is_required_for_activity=True,
            activities=[activity.uid],
            activity_subgroups=[activity_subgroup.uid],
            activity_groups=[activity_group.uid],
            activity_items=[],
            approve=False,
        )
        activity_instances.append(activity_instance)

        # Create Draft Activity
        activity_draft = TestUtils.create_activity(
            f"Activity Draft {str(idx + 1).zfill(2)}",
            activity_groups=[activity_group.uid],
            activity_subgroups=[activity_subgroup.uid],
            approve=False,
        )
        activities.append(activity_draft)

    # sort activities by name
    activities.sort(key=lambda x: x.name)


def test_get_library_activities(api_client):
    response = api_client.get(f"{BASE_URL}/library/activities")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item, LIBRARY_ACTIVITY_FIELDS_ALL, LIBRARY_ACTIVITY_FIELDS_NOT_NULL
        )

        assert item["library"] in ["Sponsor", "Requested"]
        assert item["status"] in ["Final", "Draft", "Retired"]
        assert item["groupings"][0]["activity_group_name"] == activity_group.name
        assert item["groupings"][0]["activity_subgroup_name"] == activity_subgroup.name


def test_get_library_activities_pagination_sorting(api_client):

    # Default page size
    response = api_client.get(f"{BASE_URL}/library/activities")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/library/activities?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default sort_by
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=10&sort_by=uid")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/library/activities?sort_order=desc&sort_by=uid&page_size=15"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 15
    TestUtils.assert_sort_order(res["items"], "uid", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_library_activities_all(api_client, page_size):
    all_fetched_activities = []

    response = api_client.get(f"{BASE_URL}/library/activities?page_size={page_size}")
    all_fetched_activities.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_activities.extend(response.json()["items"])

    assert len(all_fetched_activities) == len(activities)
    assert {activity["name"] for activity in all_fetched_activities} == {
        activity.name for activity in activities
    }

    TestUtils.assert_sort_order(all_fetched_activities, "name", False)


def test_get_library_activities_filtering(api_client):
    # Filter by status
    response = api_client.get(f"{BASE_URL}/library/activities?status=Final")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Final&" in res[key]

    assert len(res["items"]) == len(activities) // 2
    for item in res["items"]:
        assert item["status"] == "Final"

    response = api_client.get(f"{BASE_URL}/library/activities?status=Draft")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Draft&" in res[key]

    assert len(res["items"]) == len(activities) // 2
    for item in res["items"]:
        assert item["status"] == "Draft"

    # Filter by library
    response = api_client.get(f"{BASE_URL}/library/activities?library=Sponsor")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]

    assert len(res["items"]) == len(activities)
    for item in res["items"]:
        assert item["library"] == "Sponsor"

    response = api_client.get(f"{BASE_URL}/library/activities?library=Requested")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Requested&" in res[key]

    assert len(res["items"]) == 0
    for item in res["items"]:
        assert item["library"] == "Requested"

    # Filter by library and status
    response = api_client.get(
        f"{BASE_URL}/library/activities?library=Sponsor&status=Final"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]
        assert "status=Final&" in res[key]

    assert len(res["items"]) == len(activities) // 2
    for item in res["items"]:
        assert item["library"] == "Sponsor"
        assert item["status"] == "Final"


def test_get_library_activities_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/library/activities?page_size=0")
    assert_response_status_code(response, 422)
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_size={settings.max_page_size + 1}"
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_number={settings.max_int_neo4j + 1}&page_size=1"
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["message"]
        == f"(page_number * page_size) value cannot be bigger than {settings.max_int_neo4j}"
    )


def test_get_library_activity_instances(api_client):
    response = api_client.get(f"{BASE_URL}/library/activity-instances")
    assert_response_status_code(response, 200)
    res = response.json()

    TestUtils.assert_paginated_response_shape_ok(res, False)

    for item in res["items"]:
        TestUtils.assert_response_shape_ok(
            item,
            LIBRARY_ACTIVITY_INSTANCE_FIELDS_ALL,
            LIBRARY_ACTIVITY_INSTANCE_FIELDS_NOT_NULL,
        )

        assert item["library"] in ["Sponsor", "Requested"]
        assert item["status"] in ["Final", "Draft", "Retired"]
        assert item["groupings"][0]["activity_group_name"] == activity_group.name
        assert item["groupings"][0]["activity_subgroup_name"] == activity_subgroup.name


def test_get_library_activity_instances_pagination_sorting(api_client):

    # Default page size
    response = api_client.get(f"{BASE_URL}/library/activity-instances")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activity-instances?page_size=2")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 2
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page size
    response = api_client.get(f"{BASE_URL}/library/activity-instances?page_size=100")
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == len(activities)
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default page number and page size
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size=3&page_number=2"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 3
    TestUtils.assert_sort_order(res["items"], "name", False)

    # Non-default sort_by
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size=10&sort_by=uid"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)
    assert len(res["items"]) == 10
    TestUtils.assert_sort_order(res["items"], "uid", False)

    # Non-default sort_by and sort_order
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?sort_order=desc&sort_by=uid&page_size=15"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    assert res.keys() == {"self", "next", "prev", "items"}
    assert len(res["items"]) == 15
    TestUtils.assert_sort_order(res["items"], "uid", True)


@pytest.mark.parametrize("page_size", [8, 20, 100])
def test_get_library_activity_instances_all(api_client, page_size):
    all_fetched_activity_instances = []

    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?page_size={page_size}"
    )
    all_fetched_activity_instances.extend(response.json()["items"])

    while response.json()["items"]:
        # Fetch the next page until no items are returned
        response = api_client.get(response.json()["next"])
        all_fetched_activity_instances.extend(response.json()["items"])

    assert len(all_fetched_activity_instances) == len(activity_instances)
    assert {
        activity_inst["name"] for activity_inst in all_fetched_activity_instances
    } == {activity_inst.name for activity_inst in activity_instances}

    TestUtils.assert_sort_order(all_fetched_activity_instances, "name", False)


def test_get_library_activity_instances_filtering(api_client):
    # Filter by status
    response = api_client.get(f"{BASE_URL}/library/activity-instances?status=Final")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Final&" in res[key]

    assert len(res["items"]) == len(activity_instances) // 2
    for item in res["items"]:
        assert item["status"] == "Final"

    response = api_client.get(f"{BASE_URL}/library/activity-instances?status=Draft")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "status=Draft&" in res[key]

    assert len(res["items"]) == len(activity_instances) // 2
    for item in res["items"]:
        assert item["status"] == "Draft"

    # Filter by library
    response = api_client.get(f"{BASE_URL}/library/activity-instances?library=Sponsor")
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]

    assert len(res["items"]) == len(activity_instances)
    for item in res["items"]:
        assert item["library"] == "Sponsor"

    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?library=Requested"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Requested&" in res[key]

    assert len(res["items"]) == 0
    for item in res["items"]:
        assert item["library"] == "Requested"

    # Filter by library and status
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?library=Sponsor&status=Final"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert "library=Sponsor&" in res[key]
        assert "status=Final&" in res[key]

    assert len(res["items"]) == len(activity_instances) // 2
    for item in res["items"]:
        assert item["library"] == "Sponsor"
        assert item["status"] == "Final"

    # Filter by activity_uid
    activity_uid = activities[0].uid
    response = api_client.get(
        f"{BASE_URL}/library/activity-instances?activity_uid={activity_uid}"
    )
    assert_response_status_code(response, 200)
    res = response.json()
    TestUtils.assert_paginated_response_shape_ok(res, False)

    for key in ["self", "prev", "next"]:
        assert f"activity_uid={activity_uid}&" in res[key]

    assert len(res["items"]) == 2  # One Final and one Draft activity instance
    for item in res["items"]:
        assert item["library"] == "Sponsor"
        assert item["groupings"][0]["activity_uid"] == activity_uid
        assert item["groupings"][0]["activity_group_uid"] == activity_group.uid
        assert item["groupings"][0]["activity_subgroup_uid"] == activity_subgroup.uid


def test_get_library_activity_instances_invalid_pagination_params(api_client):
    response = api_client.get(f"{BASE_URL}/library/activity-instances?page_size=0")
    assert_response_status_code(response, 422)
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be greater than or equal to 1"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_size={settings.max_page_size + 1}"
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["detail"][0]["msg"]
        == "Input should be less than or equal to 1000"
    )

    response = api_client.get(
        f"{BASE_URL}/studies?page_number={settings.max_int_neo4j + 1}&page_size=1"
    )
    assert_response_status_code(response, 422)
    assert (
        response.json()["message"]
        == f"(page_number * page_size) value cannot be bigger than {settings.max_int_neo4j}"
    )
