"""dataset scenarios router."""

from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from pydantic.types import Json
from starlette.requests import Request

from clinical_mdr_api.models.standard_data_models.dataset_scenario import (
    DatasetScenario,
)
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions, decorators
from clinical_mdr_api.services.standard_data_models.dataset_scenario import (
    DatasetScenarioService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

router = APIRouter()

DatasetScenarioUID = Path(description="The unique id of the DatasetScenario")


@router.get(
    "/dataset-scenarios",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="List all dataset-scenarios",
    description=f"""
State before:

Business logic:
 - List all dataset scenarios in their latest version.

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
def get_dataset_scenarios(
    request: Request,  # request is actually required by the allow_exports decorator
    data_model_ig_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model IG, for instance 'SDTMIG'",
        ),
    ],
    data_model_ig_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model IG, for instance '1.4'",
        ),
    ],
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
) -> CustomPage[DatasetScenario]:
    dataset_scenario_service = DatasetScenarioService()
    results = dataset_scenario_service.get_all_items(
        sort_by=sort_by,
        page_number=page_number,
        page_size=page_size,
        total_count=total_count,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
    )
    return CustomPage(
        items=results.items, total=results.total, page=page_number, size=page_size
    )


@router.get(
    "/dataset-scenarios/headers",
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
    data_model_ig_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model IG, for instance 'SDTMIG'",
        ),
    ],
    data_model_ig_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model IG, for instance '1.4'",
        ),
    ],
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
    dataset_scenario_service = DatasetScenarioService()
    return dataset_scenario_service.get_distinct_values_for_header(
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/dataset-scenarios/{dataset_scenario_uid}",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get details on a specific dataset scenario",
    description="""
State before:
 - a dataset scenario with uid must exist.

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
def get_dataset_scenario(
    dataset_scenario_uid: Annotated[str, DatasetScenarioUID],
    data_model_ig_name: Annotated[
        str,
        Query(
            description="The name of the selected Data model IG, for instance 'SDTMIG'",
        ),
    ],
    data_model_ig_version: Annotated[
        str,
        Query(
            description="The version of the selected Data model IG, for instance '1.4'",
        ),
    ],
) -> DatasetScenario:
    dataset_scenario_service = DatasetScenarioService()
    return dataset_scenario_service.get_by_uid(
        uid=dataset_scenario_uid,
        data_model_ig_name=data_model_ig_name,
        data_model_ig_version=data_model_ig_version,
    )
