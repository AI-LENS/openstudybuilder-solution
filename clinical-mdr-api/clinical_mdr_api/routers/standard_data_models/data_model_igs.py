"""Data model IGs router."""

from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.data_model_ig import DataModelIG
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.data_model_ig import (
    DataModelIGService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/standards"
router = APIRouter()

DataModelIGUID = Path(description="The unique id of the DataModelIG")


@router.get(
    "/data-model-igs",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all data model implementation guides",
    description=f"""
State before:

Business logic:
 - List all data models in their latest version.

State after:
 - No change

{_generic_descriptions.DATA_EXPORTS_HEADER}
""",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
@decorators.allow_exports(
    {
        "defaults": ["uid", "name", "start_date", "status", "version"],
        "formats": [
            "text/csv",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            "text/xml",
            "application/json",
        ],
    }
)
# pylint: disable=unused-argument
def get_data_model_igs(
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
) -> CustomPage[DataModelIG]:
    data_model_ig_service = DataModelIGService()
    results = data_model_ig_service.get_all_items(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/data-model-igs/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="Allowed parameters include : field name for which to get possible values, "
    "search string to provide filtering for the field name, additional filters to apply on other fields",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - Invalid field name specified",
        },
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
    data_model_ig_service = DataModelIGService()
    return data_model_ig_service.get_distinct_values_for_header(
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/data-model-igs/{data_model_ig_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific data mode implementation guide",
    description="""
State before:
 - a data model implementation guide with uid must exist.

Business logic:

State after:
 - No change

Possible errors:
 - Invalid uid.
 """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_data_model(data_model_ig_uid: Annotated[str, DataModelIGUID]) -> DataModelIG:
    data_model_ig_service = DataModelIGService()
    return data_model_ig_service.get_by_uid(uid=data_model_ig_uid)
