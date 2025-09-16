from typing import Annotated, Any

from fastapi import APIRouter, Path, Query
from pydantic.types import Json

from clinical_mdr_api.models.concepts.odms.odm_description import OdmDescription
from clinical_mdr_api.models.utils import CustomPage
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.routers import _generic_descriptions
from clinical_mdr_api.services.concepts.odms.odm_descriptions import (
    OdmDescriptionService,
)
from common.auth import rbac
from common.auth.dependencies import security
from common.config import settings
from common.models.error import ErrorResponse

# Prefixed with "/concepts/odms/descriptions"
router = APIRouter()

# Argument definitions
OdmDescriptionUID = Path(description="The unique id of the ODM Description.")


@router.get(
    "",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Return a listing of ODM Descriptions",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_all_odm_descriptions(
    library_name: Annotated[str | None, Query()] = None,
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
) -> CustomPage[OdmDescription]:
    odm_description_service = OdmDescriptionService()
    results = odm_description_service.get_all_concepts(
        library=library_name,
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
    "/headers",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Returns possible values from the database for a given header",
    description="""Allowed parameters include : field name for which to get possible
    values, search string to provide filtering for the field name, additional filters to apply on other fields""",
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
    library_name: Annotated[str | None, Query()] = None,
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
    odm_description_service = OdmDescriptionService()
    return odm_description_service.get_distinct_values_for_header(
        library=library_name,
        field_name=field_name,
        search_string=search_string,
        filter_by=filters,
        filter_operator=FilterOperator.from_str(operator),
        page_size=page_size,
    )


@router.get(
    "/{odm_description_uid}/relationships",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Get UIDs of a specific ODM Description's relationships",
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: _generic_descriptions.ERROR_404,
    },
)
def get_active_relationships(
    odm_description_uid: Annotated[str, OdmDescriptionUID],
) -> dict[str, list[str]]:
    odm_description_service = OdmDescriptionService()
    return odm_description_service.get_active_relationships(uid=odm_description_uid)


@router.get(
    "/{odm_description_uid}/versions",
    dependencies=[security, rbac.LIBRARY_READ],
    summary="Return a listing of versions of a specific ODM Description",
    description="""
State before:
 - uid must exist.

Business logic:
 - List version history for ODM Descriptions.
 - The returned versions are ordered by start_date descending (newest entries first).

State after:
 - No change

Possible errors:
 - Invalid uid.
    """,
    status_code=200,
    responses={
        403: _generic_descriptions.ERROR_403,
        404: {
            "model": ErrorResponse,
            "description": "Not Found - The ODM Description with the specified 'odm_description_uid' wasn't found.",
        },
    },
)
def get_odm_description_versions(
    odm_description_uid: Annotated[str, OdmDescriptionUID],
) -> list[OdmDescription]:
    odm_description_service = OdmDescriptionService()
    return odm_description_service.get_version_history(uid=odm_description_uid)


# @router.post(
#     "",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Create a new ODM Description",
#     status_code=201,
#     responses={
#         201: {"description": "Created - The ODM Description was successfully created."},
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The library doesn't exist.\n"
#             "- The library doesn't allow to add new items.\n",
#         },
#         409: _generic_descriptions.ERROR_409,
#
#     },
# )
# def create_odm_description(
#     odm_description_create_input: Annotated[OdmDescriptionPostInput, Body()],
# ) -> OdmDescription:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.create(concept_input=odm_description_create_input)


# @router.post(
#     "/batch",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Batch operations (create, edit) for ODM Descriptions",
#     status_code=207,
#     responses={
#         404: _generic_descriptions.ERROR_404,
#
#     },
# )
# def odm_description_batch_operations(
#     operations: Annotated[
#         list[OdmDescriptionBatchInput], Body(description="List of operation to perform")
#     ]
# ) -> list[OdmDescriptionBatchOutput]:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.handle_batch_operations(operations)


# @router.patch(
#     "/{odm_description_uid}",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Update an ODM Description",
#     status_code=200,
#     responses={
#         200: {"description": "OK."},
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The ODM Description is not in draft status.\n"
#             "- The ODM Description had been in 'Final' status before.\n"
#             "- The library doesn't allow to edit draft versions.\n",
#         },
#         404: {
#             "model": ErrorResponse,
#             "description": "Not Found - The ODM Description with the specified 'odm_description_uid' wasn't found.",
#         },
#
#     },
# )
# def edit_odm_description(
#     odm_description_uid: Annotated[str, OdmDescriptionUID],
#     odm_description_edit_input: Annotated[OdmDescriptionPatchInput, Body()],
# ) -> OdmDescription:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.edit_draft(
#         uid=odm_description_uid, concept_edit_input=odm_description_edit_input
#     )


# @router.post(
#     "/{odm_description_uid}/versions",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Create a new version of an ODM Description",
#     description="""
# State before:
#  - uid must exist and the ODM Description must be in status Final.

# Business logic:
# - The ODM Description is changed to a draft state.

# State after:
#  - ODM Description changed status to Draft and assigned a new minor version number.
#  - Audit trail entry must be made with action of creating a new draft version.

# Possible errors:
#  - Invalid uid or status not Final.
# """,
#     status_code=201,
#     responses={
#         201: {"description": "OK."},
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The library doesn't allow to create ODM Descriptions.\n",
#         },
#         404: {
#             "model": ErrorResponse,
#             "description": "Not Found - Reasons include e.g.: \n"
#             "- The ODM Description is not in final status.\n"
#             "- The ODM Description with the specified 'odm_description_uid' could not be found.",
#         },
#
#     },
# )
# def create_odm_description_version(
#     odm_description_uid: Annotated[str, OdmDescriptionUID]
# ) -> OdmDescription:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.create_new_version(uid=odm_description_uid)


# @router.post(
#     "/{odm_description_uid}/approvals",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Approve an ODM Description",
#     status_code=201,
#     responses={
#         201: {"description": "OK."},
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The ODM Description is not in draft status.\n"
#             "- The library doesn't allow to approve ODM Description.\n",
#         },
#         404: {
#             "model": ErrorResponse,
#             "description": "Not Found - The ODM Description with the specified 'odm_description_uid' wasn't found.",
#         },
#
#     },
# )
# def approve_odm_description(odm_description_uid: Annotated[str, OdmDescriptionUID]) -> OdmDescription:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.approve(uid=odm_description_uid)


# @router.delete(
#     "/{odm_description_uid}/activations",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary=" Inactivate an ODM Description",
#     status_code=200,
#     responses={
#         200: {"description": "OK."},
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The ODM Description is not in final status.",
#         },
#         404: {
#             "model": ErrorResponse,
#             "description": "Not Found - The ODM Description with the specified 'odm_description_uid' could not be found.",
#         },
#
#     },
# )
# def inactivate_odm_description(odm_description_uid: Annotated[str, OdmDescriptionUID]) -> OdmDescription:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.inactivate_final(uid=odm_description_uid)


# @router.post(
#     "/{odm_description_uid}/activations",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Reactivate an ODM Description",
#     status_code=200,
#     responses={
#         200: {"description": "OK."},
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The ODM Description is not in retired status.",
#         },
#         404: {
#             "model": ErrorResponse,
#             "description": "Not Found - The ODM Description with the specified 'odm_description_uid' could not be found.",
#         },
#
#     },
# )
# def reactivate_odm_description(odm_description_uid: Annotated[str, OdmDescriptionUID]) -> OdmDescription:
#     odm_description_service = OdmDescriptionService()
#     return odm_description_service.reactivate_retired(uid=odm_description_uid)


# @router.delete(
#     "/{odm_description_uid}",
#     dependencies=[security, rbac.LIBRARY_WRITE],
#     summary="Delete draft version of ODM Description",
#     status_code=204,
#     responses={
#         204: {
#             "description": "No Content - The ODM Description was successfully deleted."
#         },
#         400: {
#             "model": ErrorResponse,
#             "description": "Forbidden - Reasons include e.g.: \n"
#             "- The ODM Description is not in draft status.\n"
#             "- The ODM Description was already in final state or is in use.\n"
#             "- The library doesn't allow to delete ODM Description.",
#         },
#         404: {
#             "model": ErrorResponse,
#             "description": "Not Found - An ODM Description with the specified 'odm_description_uid' could not be found.",
#         },
#
#     },
# )
# def delete_odm_description(odm_description_uid: Annotated[str, OdmDescriptionUID]):
#     odm_description_service = OdmDescriptionService()
#     odm_description_service.soft_delete(uid=odm_description_uid)
