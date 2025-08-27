import pytest

from common import exceptions
from common.config import settings
from common.utils import (
    filter_sort_valid_keys_re,
    load_env,
    strtobool,
    validate_page_number_and_page_size,
)


def test_strtobool():
    assert strtobool("True") == 1
    assert strtobool("true") == 1
    assert strtobool("TRUE") == 1
    assert strtobool("t") == 1
    assert strtobool("T") == 1
    assert strtobool("1") == 1

    assert strtobool("False") == 0
    assert strtobool("false") == 0
    assert strtobool("FALSE") == 0
    assert strtobool("f") == 0
    assert strtobool("F") == 0
    assert strtobool("0") == 0

    with pytest.raises(ValueError) as exc_info:
        strtobool("-invalid-")
    assert str(exc_info.value) == "invalid truth value: -invalid-"


@pytest.mark.parametrize(
    "page_number, page_size",
    [[1, 10], [2, 200], [3000, 1000], [settings.max_int_neo4j, 1]],
)
def test_validate_page_number_and_page_size(page_number, page_size):
    validate_page_number_and_page_size(page_number, page_size)


@pytest.mark.parametrize(
    "page_number, page_size",
    [
        [settings.max_int_neo4j + 1, 1],
        [settings.max_int_neo4j, 10],
        [1, settings.max_int_neo4j + 1],
        [10, settings.max_int_neo4j],
    ],
)
def test_validate_page_number_and_page_size_negative(page_number, page_size):
    with pytest.raises(exceptions.ValidationException) as exc_info:
        validate_page_number_and_page_size(page_number, page_size)
    assert (
        str(exc_info.value)
        == f"(page_number * page_size) value cannot be bigger than {settings.max_int_neo4j}"
    )


def test_load_env():
    env_var1 = load_env("VAR1", "value1")
    assert env_var1 == "value1"

    env_var1 = load_env("VAR1", "")
    assert env_var1 == ""

    with pytest.raises(EnvironmentError) as exc_info:
        load_env("VAR1")
    assert str(exc_info.value) == "Failed because VAR1 is not set."


@pytest.mark.parametrize(
    "valid_key",
    [
        "name",
        "user.name",
        "user_profile.address.city",
        "activity_groupings[0].activity_group_name",
        "a",
        "a_b.c_d[10].e_f",
        "foo[123]",
        "foo.bar[0].baz123",
        "_under_score__",
    ],
)
def test_valid_filter_sort_keys(valid_key):
    assert filter_sort_valid_keys_re.match(valid_key), f"Expected to match: {valid_key}"


@pytest.mark.parametrize(
    "invalid_key",
    [
        # Cypher injection patterns
        "name RETURN 1",
        "user.name;",
        "uid {",
        "uid, {",
        "uid CALL",
        "uid, CALL",
        "user.name WHERE 1=1",
        "user.name OR 1=1",
        "user.name OR true",
        "user.name, MATCH (n)",
        "user.name, CALL db.labels()",
        "user.name, `MATCH (n)`",
        "name + sleep(10)",
        "name + toUpper('X')",
        "__proto__",
        "user[0].name + OR 1=1",
        "user[0].name + ' OR 1=1'",
        "name--comment",
        "name//",
        "name/*",
        "user.name/",  # slash not allowed
        "user..name",  # double dot
        "1abc",  # starts with digit
        "__abc",  # starts with double underscore
        "hello.",  # ends with dot
        "user-name",  # dash not allowed
        "user name",  # space not allowed
        "user[name]",  # brackets without index
        "user[abc]",  # non-numeric index
        "user[1a]",  # malformed index
    ],
)
def test_invalid_filter_sort_keys(invalid_key):
    assert not filter_sort_valid_keys_re.match(
        invalid_key
    ), f"Expected NOT to match: {invalid_key}"
