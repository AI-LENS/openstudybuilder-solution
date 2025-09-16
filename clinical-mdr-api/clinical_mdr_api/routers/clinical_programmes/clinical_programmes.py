from typing import Annotated, Any

from fastapi import APIRouter, Body, Path, Query, Request
from pydantic.types import Json

from clinical_mdr_api.models.clinical_programmes.clinical_programme import (
    ClinicalProgramme,
    ClinicalProgrammeInput,
)
from clinical_mdr_api.models.utils import GenericFilteringReturn
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.clinical_programmes.clinical_programme import (
    ClinicalProgrammeService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/clinical-programmes"
router = APIRouter()
ClinicalProgrammeUID = Path(description="The unique id of the clinical programme.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns all clinical programmes.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_programmes(
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
) -> GenericFilteringReturn[ClinicalProgramme]:
    service = ClinicalProgrammeService()
    return service.get_all_clinical_programmes(
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
    service = ClinicalProgrammeService()
    return service.get_clinical_programme_headers(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{clinical_programme_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get a clinical programme.",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get(
    clinical_programme_uid: Annotated[str, ClinicalProgrammeUID],
) -> ClinicalProgramme:
    service = ClinicalProgrammeService()
    return service.get_clinical_programme_by_uid(clinical_programme_uid)


@router.post(
    "",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Creates a new clinical programme.",
    status_code=201,
    responses={
        403: _generic_descriptions.ERROR_403,
        201: {
            "description": "Created - The clinical programme was successfully created."
        },
    },
)
# pylint: disable=unused-argument
def create(
    clinical_programme_create_input: Annotated[
        ClinicalProgrammeInput,
        Body(
            description="Related parameters of the clinical programme that shall be created.",
        ),
    ],
) -> ClinicalProgramme:
    service = ClinicalProgrammeService()
    return service.create(clinical_programme_create_input)


@router.patch(
    "/{clinical_programme_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Edit a clinical programme.",
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
    clinical_programme_uid: Annotated[str, ClinicalProgrammeUID],
    clinical_programme_edit_input: Annotated[ClinicalProgrammeInput, Body()],
) -> ClinicalProgramme:
    service = ClinicalProgrammeService()
    return service.edit(clinical_programme_uid, clinical_programme_edit_input)


@router.delete(
    "/{clinical_programme_uid}",
    dependencies=[security, rbac.LIBRARY_WRITE],
    summary="Delete a clinical programme.",
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
def delete(clinical_programme_uid: Annotated[str, ClinicalProgrammeUID]):
    service = ClinicalProgrammeService()
    return service.delete(clinical_programme_uid)
