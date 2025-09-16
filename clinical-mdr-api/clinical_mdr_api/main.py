"""Application main file."""

# Placed at the top to ensure logging is configured before anything else is loaded
from common.logger import default_logging_config, log_exception

default_logging_config()

# pylint: disable=wrong-import-position,wrong-import-order,ungrouped-imports
import logging
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from opencensus.ext.azure.trace_exporter import AzureExporter
from opencensus.trace.print_exporter import PrintExporter
from opencensus.trace.samplers import AlwaysOnSampler
from pydantic import ValidationError
from starlette.middleware import Middleware
from starlette_context.middleware import RawContextMiddleware

from clinical_mdr_api.utils.api_version import get_api_version
from common.auth.dependencies import security
from common.auth.discovery import reconfigure_with_openid_discovery
from common.config import settings
from common.exceptions import MDRApiBaseException
from common.models.error import ErrorResponse
from common.telemetry.request_metrics import patch_neomodel_database
from common.telemetry.traceback_middleware import ExceptionTracebackMiddleware
from common.telemetry.tracing_middleware import TracingMiddleware

log = logging.getLogger(__name__)


# Middlewares - please don't use app.add_middleware() as that inserts them to the beginning of the list
middlewares = []

# gzip compress responses
if settings.gzip_response_min_size:
    middlewares.append(
        Middleware(
            GZipMiddleware,
            minimum_size=settings.gzip_response_min_size,
            compresslevel=settings.gzip_level,
        )
    )

# Context middleware - must come before TracingMiddleware
middlewares.append(Middleware(RawContextMiddleware))

# Tracing middleware
if settings.tracing_enabled:

    # Azure Application Insights integration for tracing
    if settings.appinsights_connection:
        tracing_exporter = AzureExporter(
            connection_string=settings.appinsights_connection,
            enable_local_storage=False,
        )

    elif settings.zipkin_host:
        # opencensus-ext-zipkin is a dev-only package dependency
        from opencensus.ext.zipkin.trace_exporter import ZipkinExporter

        tracing_exporter = ZipkinExporter(
            service_name="clinical-mdr-api",
            host_name=settings.zipkin_host,
            port=settings.zipkin_port,
            endpoint=settings.zipkin_endpoint,
            protocol=settings.zipkin_protocol,
        )

    else:
        tracing_exporter = PrintExporter()

    middlewares.append(
        Middleware(
            TracingMiddleware,
            sampler=AlwaysOnSampler(),
            exporter=tracing_exporter,
            exclude_paths={"*/system/healthcheck"},
        )
    )

    patch_neomodel_database()


middlewares.append(
    Middleware(
        CORSMiddleware,
        allow_origin_regex=settings.allow_origin_regex,
        allow_credentials=settings.allow_credentials,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
        expose_headers=["traceresponse"],
    )
)

# Convert all uncaught exceptions to response before returning to TracingMiddleware
middlewares.append(Middleware(ExceptionTracebackMiddleware))


@asynccontextmanager
async def lifespan(_app: FastAPI):
    if settings.oauth_enabled:
        # Reconfiguring Swagger UI settings with OpenID Connect discovery
        await reconfigure_with_openid_discovery()
    yield


app = FastAPI(
    title=settings.app_name,
    middleware=middlewares,
    lifespan=lifespan,
    swagger_ui_init_oauth=settings.swagger_ui_init_oauth,
    version=get_api_version(),
    swagger_ui_parameters={"docExpansion": "none"},
    description="""
## NOTICE

This license information is applicable to the swagger documentation of the clinical-mdr-api, that is the openapi.json.

## License Terms (MIT)

Copyright (C) 2025 Novo Nordisk A/S, Danish company registration no. 24256790

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Licenses and Acknowledgements for Incorporated Software

This component contains software licensed under different licenses when compiled, please refer to the third-party-licenses.md file for further information and full license texts.

## Authentication

Supports OAuth2 [Authorization Code Flow](https://datatracker.ietf.org/doc/html/rfc6749#section-4.1),
at paths described in the OpenID Connect Discovery metadata document (whose URL is defined by the `OAUTH_METADATA_URL` environment variable).

Microsoft Identity Platform documentation can be read 
([here](https://docs.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)).

Authentication can be turned off with `OAUTH_ENABLED=false` environment variable. 

When authentication is turned on, all requests to protected API endpoints must provide a valid bearer (JWT) token inside the `Authorization` http header. 
""",
)

# TODO: This is a temporary workaround as schemathesis doesnt support openapi 3.1.0 yet; this should be removed when schemathesis supports 3.1.0
app.openapi_version = "3.0.2"


@app.exception_handler(MDRApiBaseException)
async def mdr_api_exception_handler(request: Request, exception: MDRApiBaseException):
    """Returns an HTTP error code associated to given exception."""

    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=exception.status_code,
        content=jsonable_encoder(ErrorResponse(request, exception)),
        headers=exception.headers,
    )


@app.exception_handler(ValidationError)
async def pydantic_validation_error_handler(
    request: Request, exception: ValidationError
):
    """Returns `400 Bad Request` http error status code in case Pydantic detects validation issues
    with supplied payloads or parameters."""

    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ErrorResponse(request, exception)),
    )


@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exception: ValueError):
    """Returns `400 Bad Request` http error status code in case ValueError is raised"""

    await log_exception(request, exception)

    ExceptionTracebackMiddleware.add_traceback_attributes(exception)

    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=jsonable_encoder(ErrorResponse(request, exception)),
    )


# Late import of routers, because they do run code on import, and we want monkey-patching like tracing to work
# pylint: disable=wrong-import-position,ungrouped-imports
from clinical_mdr_api import routers

# Include routers here
app.include_router(routers.system_router, tags=["System"])

app.include_router(
    routers.feature_flags_router,
    prefix="/feature-flags",
    tags=["Feature Flags"],
)
app.include_router(
    routers.notifications_router,
    prefix="/notifications",
    tags=["Notifications"],
)
app.include_router(
    routers.odm_study_events_router,
    prefix="/concepts/odms/study-events",
    tags=["ODM Study Events"],
)
app.include_router(
    routers.odm_forms_router, prefix="/concepts/odms/forms", tags=["ODM Forms"]
)
app.include_router(
    routers.odm_item_groups_router,
    prefix="/concepts/odms/item-groups",
    tags=["ODM Item Groups"],
)
app.include_router(
    routers.odm_item_router, prefix="/concepts/odms/items", tags=["ODM Item"]
)
app.include_router(
    routers.odm_conditions_router,
    prefix="/concepts/odms/conditions",
    tags=["ODM Conditions"],
)
app.include_router(
    routers.odm_methods_router,
    prefix="/concepts/odms/methods",
    tags=["ODM Methods"],
)
app.include_router(
    routers.odm_formal_expressions_router,
    prefix="/concepts/odms/formal-expressions",
    tags=["ODM Formal Expressions"],
)
app.include_router(
    routers.odm_descriptions_router,
    prefix="/concepts/odms/descriptions",
    tags=["ODM Descriptions"],
)
app.include_router(
    routers.odm_aliases_router, prefix="/concepts/odms/aliases", tags=["ODM Aliases"]
)
app.include_router(
    routers.odm_vendor_namespace_router,
    prefix="/concepts/odms/vendor-namespaces",
    tags=["ODM Vendor Namespaces"],
)
app.include_router(
    routers.odm_vendor_attribute_router,
    prefix="/concepts/odms/vendor-attributes",
    tags=["ODM Vendor Attributes"],
)
app.include_router(
    routers.odm_vendor_element_router,
    prefix="/concepts/odms/vendor-elements",
    tags=["ODM Vendor Elements"],
)
app.include_router(
    routers.odm_metadata_router,
    prefix="/concepts/odms/metadata",
    tags=["ODM Metadata Import/Export"],
)
app.include_router(
    routers.activity_instruction_templates_router,
    prefix="/activity-instruction-templates",
    tags=["Activity Instruction Templates"],
)
app.include_router(
    routers.activity_instructions_router,
    prefix="/activity-instructions",
    tags=["Activity Instructions"],
)
app.include_router(
    routers.activity_instruction_pre_instances_router,
    prefix="/activity-instruction-pre-instances",
    tags=["Activity Instruction Pre-Instances"],
)
app.include_router(
    routers.footnote_templates_router,
    prefix="/footnote-templates",
    tags=["Footnote Templates"],
)
app.include_router(routers.footnote_router, prefix="/footnotes", tags=["Footnotes"])
app.include_router(
    routers.footnote_pre_instances_router,
    prefix="/footnote-pre-instances",
    tags=["Footnote Pre-Instances"],
)
app.include_router(
    routers.criteria_templates_router,
    prefix="/criteria-templates",
    tags=["Criteria Templates"],
)
app.include_router(
    routers.criteria_pre_instances_router,
    prefix="/criteria-pre-instances",
    tags=["Criteria Pre-Instances"],
)
app.include_router(routers.criteria_router, prefix="/criteria", tags=["Criteria"])
app.include_router(
    routers.objective_templates_router,
    prefix="/objective-templates",
    tags=["Objective Templates"],
)
app.include_router(
    routers.objective_pre_instances_router,
    prefix="/objective-pre-instances",
    tags=["Objective Pre-Instances"],
)
app.include_router(routers.objectives_router, prefix="/objectives", tags=["Objectives"])
app.include_router(
    routers.endpoint_templates_router,
    prefix="/endpoint-templates",
    tags=["Endpoint Templates"],
)
app.include_router(
    routers.endpoint_pre_instances_router,
    prefix="/endpoint-pre-instances",
    tags=["Endpoint Pre-Instances"],
)
app.include_router(routers.endpoints_router, prefix="/endpoints", tags=["Endpoints"])
app.include_router(
    routers.timeframe_templates_router,
    prefix="/timeframe-templates",
    tags=["Timeframe templates"],
)
app.include_router(routers.timeframes_router, prefix="/timeframes", tags=["Timeframes"])
app.include_router(routers.libraries_router, prefix="/libraries", tags=["Libraries"])
app.include_router(routers.ct_catalogues_router, prefix="/ct", tags=["CT Catalogues"])
app.include_router(routers.ct_packages_router, prefix="/ct", tags=["CT Packages"])
app.include_router(routers.ct_codelists_router, prefix="/ct", tags=["CT Codelists"])
app.include_router(
    routers.ct_codelist_attributes_router, prefix="/ct", tags=["CT Codelists"]
)
app.include_router(
    routers.ct_codelist_names_router, prefix="/ct", tags=["CT Codelists"]
)
app.include_router(routers.ct_terms_router, prefix="/ct", tags=["CT Terms"])
app.include_router(routers.ct_term_attributes_router, prefix="/ct", tags=["CT Terms"])
app.include_router(routers.ct_term_names_router, prefix="/ct", tags=["CT Terms"])
app.include_router(routers.ct_stats_router, prefix="/ct", tags=["CT Stats"])
app.include_router(
    routers.dictionary_codelists_router,
    prefix="/dictionaries",
    tags=["Dictionary Codelists"],
)
app.include_router(
    routers.dictionary_terms_router, prefix="/dictionaries", tags=["Dictionary Terms"]
)
app.include_router(
    routers.template_parameters_router,
    prefix="/template-parameters",
    tags=["Template Parameters"],
)
app.include_router(
    routers.activity_instances_router,
    prefix="/concepts/activities/activity-instances",
    tags=["Activity Instances"],
)
app.include_router(
    routers.activity_instance_classes_router,
    prefix="/activity-instance-classes",
    tags=["Activity Instance Classes"],
)
app.include_router(
    routers.activity_item_classes_router,
    prefix="/activity-item-classes",
    tags=["Activity Item Classes"],
)
app.include_router(routers.compounds_router, prefix="/concepts", tags=["Compounds"])
app.include_router(
    routers.active_substances_router, prefix="/concepts", tags=["Active Substances"]
)
app.include_router(
    routers.pharmaceutical_products_router,
    prefix="/concepts",
    tags=["Pharmaceutical Products"],
)
app.include_router(
    routers.medicinal_products_router,
    prefix="/concepts",
    tags=["Medicinal Products"],
)
app.include_router(
    routers.compound_aliases_router, prefix="/concepts", tags=["Compound Aliases"]
)
app.include_router(
    routers.activities_router,
    prefix="/concepts/activities",
    tags=["Activities"],
)
app.include_router(
    routers.activity_subgroups_router,
    prefix="/concepts/activities",
    tags=["Activity Subgroups"],
)
app.include_router(
    routers.activity_groups_router,
    prefix="/concepts/activities",
    tags=["Activity Groups"],
)
app.include_router(
    routers.numeric_values_router,
    prefix="/concepts/numeric-values",
    tags=["Numeric Values"],
)
app.include_router(
    routers.numeric_values_with_unit_router,
    prefix="/concepts/numeric-values-with-unit",
    tags=["Numeric Values With Unit"],
)
app.include_router(
    routers.text_values_router, prefix="/concepts/text-values", tags=["Text Values"]
)
app.include_router(
    routers.visit_names_router, prefix="/concepts/visit-names", tags=["Visit Names"]
)
app.include_router(
    routers.study_days_router, prefix="/concepts/study-days", tags=["Study Days"]
)
app.include_router(
    routers.study_weeks_router, prefix="/concepts/study-weeks", tags=["Study Weeks"]
)
app.include_router(
    routers.study_duration_days_router,
    prefix="/concepts/study-duration-days",
    tags=["Study Duration Days"],
)
app.include_router(
    routers.study_duration_weeks_router,
    prefix="/concepts/study-duration-weeks",
    tags=["Study Duration Weeks"],
)
app.include_router(
    routers.time_points_router, prefix="/concepts/time-points", tags=["Time Points"]
)
app.include_router(
    routers.lag_times_router, prefix="/concepts/lag-times", tags=["Lag Times"]
)
app.include_router(routers.projects_router, prefix="/projects", tags=["Projects"])
app.include_router(
    routers.clinical_programmes_router,
    prefix="/clinical-programmes",
    tags=["Clinical Programmes"],
)
app.include_router(routers.admin_router, prefix="/admin", tags=["Admin"])
app.include_router(routers.brands_router, prefix="/brands", tags=["Brands"])
app.include_router(routers.comments_router, prefix="", tags=["Comments"])

app.include_router(routers.studies_router, prefix="/studies", tags=["Studies"])

app.include_router(routers.study_router, prefix="", tags=["Study Selections"])
app.include_router(
    routers.unit_definition_router,
    prefix="/concepts/unit-definitions",
    tags=["Unit Definitions"],
)
app.include_router(
    routers.metadata_router, prefix="/listings", tags=["Listing Metadata"]
)
app.include_router(
    routers.listing_router, prefix="/listings", tags=["Listing Legacy CDW MMA"]
)
app.include_router(
    routers.sdtm_listing_router, prefix="/listings", tags=["SDTM Study Design Listings"]
)
app.include_router(
    routers.adam_listing_router, prefix="/listings", tags=["ADaM Study Design Listings"]
)
app.include_router(
    routers.study_listing_router, prefix="/listings", tags=["Study Design Listings"]
)
app.include_router(
    routers.configuration_router,
    prefix="/configurations",
    tags=["Configurations"],
)
app.include_router(
    routers.data_models_router,
    prefix="/standards",
    tags=["Data models"],
)
app.include_router(
    routers.data_model_igs_router,
    prefix="/standards",
    tags=["Data model implementation guides"],
)
app.include_router(
    routers.sponsor_models_router,
    prefix="/standards/sponsor-models/models",
    tags=["Sponsor models"],
)
app.include_router(
    routers.sponsor_model_datasets_router,
    prefix="/standards/sponsor-models/datasets",
    tags=["Sponsor model datasets"],
)
app.include_router(
    routers.sponsor_model_dataset_variables_router,
    prefix="/standards/sponsor-models/dataset-variables",
    tags=["Sponsor model variables"],
)
app.include_router(
    routers.dataset_classes_router,
    prefix="/standards",
    tags=["Dataset classes"],
)
app.include_router(
    routers.datasets_router,
    prefix="/standards",
    tags=["Datasets"],
)
app.include_router(
    routers.dataset_scenarios_router,
    prefix="/standards",
    tags=["Dataset scenarios"],
)
app.include_router(
    routers.class_variables_router,
    prefix="/standards",
    tags=["Class variables"],
)
app.include_router(
    routers.dataset_variables_router,
    prefix="/standards",
    tags=["Dataset variables"],
)
app.include_router(
    routers.integrations.msgraph.router,
    prefix="/integrations/ms-graph",
    tags=["MS Graph API integrations"],
)
app.include_router(routers.ddf_router, prefix="/usdm/v3", tags=["USDM endpoints"])


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )

    openapi_schema["servers"] = [{"url": settings.openapi_schema_api_root_path}]

    if settings.oauth_enabled:
        if "components" not in openapi_schema:
            openapi_schema["components"] = {}

        if "securitySchemes" not in openapi_schema["components"]:
            openapi_schema["components"]["securitySchemes"] = {}

        # Add 'BearerJwtAuth' security schema globally
        openapi_schema["components"]["securitySchemes"]["BearerJwtAuth"] = {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",  # optional, arbitrary value for documentation purposes
            "in": "header",
            "name": "Authorization",
            "description": "Access token that will be sent as `Authorization: Bearer {token}` header in all requests",
        }
        openapi_schema["components"]["securitySchemes"][
            "OAuth2AuthorizationCodeBearer"
        ]["flows"]["authorizationCode"]["scopes"] = {
            "api:///API.call": "Make calls to the API"
        }

        # Add 'BearerJwtAuth' security method to all endpoints
        api_router = [route for route in app.routes if isinstance(route, APIRoute)]
        for route in api_router:
            if not any(
                dependency
                for dependency in route.dependencies
                if dependency == security
            ):
                continue

            path = getattr(route, "path")
            methods = [method.lower() for method in getattr(route, "methods")]

            for method in methods:
                endpoint_security: list[Any] = openapi_schema["paths"][path][
                    method
                ].get("security", [])
                endpoint_security.append({"BearerJwtAuth": []})
                openapi_schema["paths"][path][method]["security"] = endpoint_security

    # Add `400 Bad Request` error response to all endpoints
    for path, path_item in openapi_schema["paths"].items():
        for method, operation in path_item.items():
            if "responses" not in operation:
                operation["responses"] = {}
            if "400" not in operation["responses"]:
                operation["responses"]["400"] = {
                    "description": "Bad Request",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ErrorResponse"}
                        }
                    },
                }

    app.openapi_schema = openapi_schema
    return app.openapi_schema


setattr(app, "openapi", custom_openapi)
