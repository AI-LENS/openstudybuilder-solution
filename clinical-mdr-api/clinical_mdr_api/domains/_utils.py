from enum import Enum
from typing import Literal, overload

from clinical_mdr_api.domains.iso_languages import LANGUAGES_INDEXED_BY
from clinical_mdr_api.domains.libraries.parameter_term import ParameterTermEntryVO
from common import exceptions


class ObjectStatus(Enum):
    """
    Enum for object status.

    Possible values:
    - LATEST_FINAL: The latest final version of the object.
    - LATEST_RETIRED: The latest retired version of the object.
    - LATEST_DRAFT: The latest draft version of the object.
    - LATEST: The latest version of the object, regardless of the status.
    """

    LATEST_FINAL = "final"
    LATEST_RETIRED = "retired"
    LATEST_DRAFT = "draft"
    LATEST = "latest"


@overload
def get_iso_lang_data(
    query: str,
    key: Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] = "639-3",
    return_key: None = None,
    ignore_case: bool = True,
) -> dict[str, str | list[str]]: ...
@overload
def get_iso_lang_data(
    query: str,
    key: Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] = "639-3",
    return_key: Literal["names", "639-3"] = "names",
    ignore_case: bool = True,
) -> list[str]: ...
@overload
def get_iso_lang_data(
    query: str,
    key: Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] = "639-3",
    return_key: Literal["639-1", "639-2/T", "639-2/B"] = "639-1",
    ignore_case: bool = True,
) -> str: ...
def get_iso_lang_data(
    query: str,
    key: Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] = "639-3",
    return_key: Literal["names", "639-1", "639-2/T", "639-2/B", "639-3"] | None = None,
    ignore_case: bool = True,
) -> str | dict[str, str | list[str]] | list[str]:
    """
    Returns ISO language data based on the provided query string and key.

    Args:
        query (str): Query string to search for in the language index.
        key (str, optional): Key to use for indexing the language data. Defaults to "639-3".
        return_key (str | None, optional): Key to return from the found language data. Defaults to None.
        ignore_case (bool, optional): Whether to ignore case when searching for the query string. Defaults to True.

    Returns:
        str | dict[str, str, list[str]] | list[Any]: The value of the found language data, or the entire language data if return_key is None.

    Raises:
        TypeError: If the query string is not a string.
        ValueError: If the provided key is not a valid index for the language data.
        ValidationException: If the query string is not found in the language index, or if it is found but does not match the query when ignore_case is False.

    Example:
        >>> get_iso_lang_data("spa", "639-2/T", "names")
        ["Spanish", "Castilian"]
    """
    if not isinstance(query, str):
        raise TypeError(f"Expected type str but found {type(query)}")

    try:
        index = LANGUAGES_INDEXED_BY[key]
    except KeyError as exc:
        raise exceptions.ValidationException(
            msg=f"Languages not indexed by key: {key}"
        ) from exc

    casefolded_query = query.casefold()

    try:
        lang = index[casefolded_query]
    except KeyError as exc:
        raise exceptions.ValidationException(
            msg=f"Language '{query}' not found in {key}."
        ) from exc

    if not ignore_case and lang[key] != query:
        raise exceptions.ValidationException(
            msg=f"Language '{query}' not found in {key}."
        )

    return lang[return_key] if return_key else lang


def is_syntax_of_template_name_correct(name: str) -> bool:
    """
    Checks the syntax of the name.
    The syntax is considered to be valid if all of the following conditions are true:
    - The name consists of at least one printable character.
    - The name contains no brackets or a matching number of opening and closing brackets [].
    - The name does not contain nested brackets like this: [a[b]c].
    - The parameters within the brackets need to consist of at least one character.

    Args:
        name (str): The name of the template.

    Returns:
        bool: True if the syntax of the name is valid.
    """
    if not isinstance(name, str):
        raise TypeError(f"Expected type str but found {type(name)}")

    if len(name.strip()) == 0:
        return False

    brackets_counter = 0
    char_counter = 0
    for char in name:
        if char == "[":
            brackets_counter += 1
            char_counter = 0
        elif char == "]":
            if char_counter == 0:
                return False
            brackets_counter -= 1
            char_counter = 0
        else:
            char_counter += 1

        if brackets_counter < 0 or brackets_counter > 1:
            return False

    return brackets_counter == 0


def capitalize_first_letter_if_template_parameter(
    name: str,
    template_plain_name: str,
    parameters: list[ParameterTermEntryVO] | None = None,
) -> str:
    """
    Capitalizes the first letter of `name` if the letter is part of a template parameter which is not a Unit Definition.

    Args:
        name (str): The input string that may have its first letter capitalized.
        template_plain_name (str): The plain name of the template used to determine if capitalization is needed.

    Returns:
        str: `name` with the first letter capitalized if the letter is part of a template parameter which is not a Unit Definition.
        Otherwise, it returns `name` without any changes.
    """
    if (
        template_plain_name.startswith("[")
        and parameters
        and "UnitDefinitionRoot" not in parameters[0].parameters[0].labels
    ):
        idx = name.find("[")
        first_letter = idx + 1
        second_letter = idx + 2

        return (
            name[:first_letter]
            + name[first_letter:second_letter].upper()
            + name[second_letter:]
        )
    return name
