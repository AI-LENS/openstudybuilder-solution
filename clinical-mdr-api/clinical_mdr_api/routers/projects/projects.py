from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request
from pydantic.types import Json

from clinical_mdr_api.models.projects.project import (
    Project,
    ProjectCreateInput,
    ProjectEditInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.projects.project import ProjectService
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/projects"
router = APIRouter()


# Argument definitions
ProjectUID = Path(description="The unique id of the project.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all projects.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": [
            "uid",
            "project_number",
            "name",
            "description",
            "clinical_programme=clinical_programme.name",
        ],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_projects(
    request: Request,  # request is actually required by the allow_exports decorator
    sort_by: Annotated[
        Json | None, Query(description=_generic_descriptions.SORT_BY)
    ] = None,
    page_number: Annotated[
        int, Query(ge=1, description=_generic_descriptions.PAGE_NUMBER)
    ] = settings.default_page_number,
    page_size: Annotated[
        int,
        Query(
            ge=0,
            le=settings.max_page_size,
            description=_generic_descriptions.PAGE_SIZE,
        ),
    ] = settings.default_page_size,
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = settings.default_filter_operator,
    total_count: Annotated[
        bool, Query(description=_generic_descriptions.TOTAL_COUNT)
    ] = False,
) -> GenericFilteringReturn[Project]:
    service = ProjectService()
    return service.get_all_projects(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        total_count=total_count,
    )


@router.get(
    "/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_distinct_values_for_header(
    field_name: Annotated[
        str, Query(description=_generic_descriptions.HEADER_FIELD_NAME)
    ],
    search_string: Annotated[
        str, Query(description=_generic_descriptions.HEADER_SEARCH_STRING)
    ] = "",
    filters: Annotated[
        Json | None,
        Query(
            description=_generic_descriptions.FILTERS,
            openapi_examples=_generic_descriptions.FILTERS_EXAMPLE,
        ),
    ] = None,
    operator: Annotated[
        str, Query(description=_generic_descriptions.FILTER_OPERATOR)
    ] = settings.default_filter_operator,
    page_size: Annotated[
        int, Query(description=_generic_descriptions.HEADER_PAGE_SIZE)
    ] = settings.default_header_page_size,
) -> list[Any]:
    service = ProjectService()
    return service.get_project_headers(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{project_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a project.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get(project_uid: Annotated[str, ProjectUID]) -> Project:
    service = ProjectService()
    return service.get_project_by_uid(project_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new project.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {"description": "Created - The project was successfully created."},
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        409: _generic_descriptions.ERROR_409,
    },
)
def create(
    project_create_input: Annotated[
        ProjectCreateInput,
        Body(description="Related parameters of the project that shall be created."),
    ],
) -> Project:
    service = ProjectService()
    return service.create(project_create_input)


@router.patch(
    "/{project_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Edit a project.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
        404: _generic_descriptions.ERROR_404,
    },
)
def edit(
    project_uid: Annotated[str, ProjectUID],
    project_edit_input: Annotated[ProjectEditInput, Body()],
) -> Project:
    service = ProjectService()
    return service.edit(project_uid, project_edit_input)


@router.delete(
    "/{project_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete a project.",
    status_code=204,
    responses={
        403: _generic_descriptions.ERROR_403,
        400: {
            "model": ErrorResponse,
            "description": "Some application/business rules forbid to process the request. Expect more detailed"
            " information in response body.",
        },
    },
)
def delete(project_uid: Annotated[str, ProjectUID]):
    service = ProjectService()
    return service.delete(project_uid)
