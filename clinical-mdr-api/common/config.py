"""Configuration parameters."""

import os
import string
import urllib.parse
from typing import Any

from neomodel import config as neomodel_config
from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Settings class for the application.

    This class is responsible for:
        - providing a single point of access to all configuration parameters.
        - automatically loading configuration parameters from `.env` (as defined in region `.env variables`).
        - defining parameters that shouldn't be defined in `.env` but still available in the code (as defined in region `non-.env variables`).
        - providing type validation for the parameters.
        - providing default values for the parameters.

    Naming conventions:
        - All parameters must be in `snake_case`.
        - Parameters loaded from `.env` file that need to be post-processed must be in `UPPER_CASE` and prefixed with `ENV_`
        and a corresponding property attribute must be defined in `snake_case` with the original name (i.e. without the prefix).
        See `allow_methods` and `allow_headers` for example.
    """

    app_root_dir: str = os.path.abspath(os.path.join(os.path.dirname(__file__), "../"))

    # region .env variables
    model_config = SettingsConfigDict(
        env_file=f"{app_root_dir}/.env",
        extra="ignore",
        case_sensitive=False,
    )

    @field_validator(
        "allow_credentials",
        "oauth_enabled",
        "ms_graph_integration_enabled",
        "tracing_enabled",
        "tracing_metrics_header",
        "trace_request_body",
        mode="before",
    )
    @classmethod
    def cast_to_bool(cls, value: str | bool) -> bool:
        if isinstance(value, bool):
            return value

        return value.casefold().strip() in ("true", "1", "on", "yes", "y", "enabled")

    # Application Configuration
    app_name: str = "StudyBuilder API"
    openapi_schema_api_root_path: str = Field(default="/", alias="UVICORN_ROOT_PATH")
    app_debug: bool = False
    color_logs: bool = Field(
        default=True,
        description="Whether to color log messages based on severity when logging to console",
    )
    uid: int = 1000
    number_of_uid_digits: int = 6

    # Database Configuration
    neo4j_database: str | None = None  # deprecated, include database name in NEO4J_DSN
    neo4j_dsn: str
    neo4j_connection_lifetime: int = 29 * 60

    # Cache Configuration
    cache_max_size: int = 1000
    cache_ttl: int = 3600

    # Security & CORS
    allow_origin_regex: str | None = None
    allow_credentials: bool = True

    ENV_ALLOW_METHODS: str = Field(default="*", alias="ALLOW_METHODS")

    @property
    def allow_methods(self) -> list[str]:
        return self.ENV_ALLOW_METHODS.split(",")

    ENV_ALLOW_HEADERS: str = Field(default="*", alias="ALLOW_HEADERS")

    @property
    def allow_headers(self) -> list[str]:
        return self.ENV_ALLOW_HEADERS.split(",")

    # Pagination Configuration
    default_page_number: int = 1
    default_page_size: int = 10
    default_header_page_size: int = 10
    default_filter_operator: str = "and"
    max_page_size: int = 1000
    page_size_100: int = 100

    # Performance
    slow_query_duration: int = 1

    # Tracing & Monitoring
    uvicorn_log_config: str = ""
    tracing_enabled: bool = False
    tracing_metrics_header: bool = False
    trace_request_body: bool = False
    trace_request_body_min_status_code: int = 400
    trace_request_body_truncate_bytes: int = 2048
    trace_query_max_len: int = 4000
    traceback_max_entries: int = Field(
        default=15, description="Limit number of stack trace entries in tracebacks"
    )
    appinsights_connection: str = Field(
        default="", alias="APPLICATIONINSIGHTS_CONNECTION_STRING"
    )
    zipkin_host: str = Field(
        default="",
        description="Enable tracing to Zipkin, hostname or IP of the Zipkin service.",
    )
    zipkin_port: int = 9411
    zipkin_endpoint: str = "/api/v2/spans"
    zipkin_protocol: str = "http"

    # OAuth & Authentication
    oauth_enabled: bool = True
    oauth_rbac_enabled: bool = True
    oauth_metadata_url: str = ""
    oauth_api_app_id: str = ""
    oauth_api_app_secret: SecretStr = SecretStr("")

    ENV_OAUTH_API_APP_ID_URI: str = Field(default="", alias="OAUTH_API_APP_ID_URI")

    @property
    def oauth_api_app_id_uri(self) -> str:
        return self.ENV_OAUTH_API_APP_ID_URI or f"api://{self.oauth_api_app_id}"

    oauth_swagger_app_id: str = ""
    oauth_ui_app_id: str = ""

    # Testing & Schemathesis
    schemathesis_study_uid: str = ""
    schemathesis_hooks: str = ""

    # Third-party Integrations
    ms_graph_integration_enabled: bool = False
    ms_graph_groups_query: str = "``"

    # gzip API responses (Content-Encoding: gzip)
    gzip_response_min_size: int = Field(
        default=500,
        ge=0,
        description="Minimum response size in bytes to gzip compress, or 0 to disable.",
    )
    gzip_level: int = Field(
        default=5, ge=0, le=9, description="gzip compression level (0 to 9)"
    )

    # endregion

    # region non-.env variables
    templates_directory: str = "templates/"
    jwt_leeway_seconds: int = 10

    @property
    def our_scopes(self) -> dict[str, str]:
        return {
            f"{self.oauth_api_app_id_uri}/API.call": "Make calls to the API",
        }

    @property
    def swagger_ui_init_oauth(self) -> dict[str, Any] | None:
        return (
            {
                "usePkceWithAuthorizationCodeGrant": True,
                "clientId": self.oauth_swagger_app_id or self.oauth_api_app_id,
                "scopes": (
                    ["openid", "profile", "email", "offline_access"]
                    + list(self.our_scopes.keys())
                ),
                "additionalQueryStringParams": {
                    "response_mode": "fragment",
                },
            }
            if self.oauth_enabled
            else None
        )

    max_int_neo4j: int = 9223372036854775807

    non_visit_number: int = 29999
    unscheduled_visit_number: int = 29500
    visit_0_number: int = 0
    fixed_week_period: int = 7

    operational_soa_docx_template: str = "operational-soa-template.docx"
    xml_stylesheet_dir_path: str = "xml_stylesheets/"

    sdtm_ct_catalogue_name: str = "SDTM CT"
    adam_ct_catalogue_name: str = "ADAM CT"
    requested_library_name: str = "Requested"
    cdisc_library_name: str = "CDISC"
    ct_uid_boolean_yes: str = "C49488_Y"
    ct_uid_boolean_no: str = "C49487_N"
    ct_uid_na_value: str = "C48660_NA"
    ct_uid_positive_infinity: str = "CTTerm_000097"
    study_objective_level_name: str = "Objective Level"
    study_epoch_type_name: str = "Epoch Type"
    study_epoch_subtype_name: str = "Epoch Sub Type"
    study_epoch_epoch_name: str = "Epoch"
    basic_epoch_name: str = "Basic"
    study_epoch_epoch_uid: str = "C99079"
    study_disease_milestone_type_name: str = "Disease Milestone Type"

    special_visit_letters: str = string.ascii_uppercase
    special_visit_max_number: int = len(string.ascii_uppercase)
    study_visit_type_name: str = "VisitType"
    study_visit_type_information_visit: str = "Information"
    study_visit_repeating_frequency: str = "Repeating Visit Frequency"
    study_visit_type_early_discontinuation_visit: str = "Early discontinuation"
    study_visit_name: str = "VisitName"
    study_day_name: str = "StudyDay"
    study_duration_days_name: str = "StudyDurationDays"
    study_week_name: str = "StudyWeek"
    study_duration_weeks_name: str = "StudyDurationWeeks"
    week_in_study_name: str = "WeekInStudy"
    study_timepoint_name: str = "TimePoint"
    study_visit_timeref_name: str = "Time Point Reference"
    study_element_subtype_name: str = "Element Sub Type"
    global_anchor_visit_name: str = "Global anchor visit"
    previous_visit_name: str = "Previous Visit"
    anchor_visit_in_visit_group: str = "Anchor visit in visit group"
    study_endpoint_level_name: str = "Endpoint Level"
    study_endpoint_tp_name: str = "StudyEndpoint"
    study_field_preferred_time_unit_name: str = "preferred_time_unit"
    study_field_soa_preferred_time_unit_name: str = "soa_preferred_time_unit"
    study_field_soa_show_epochs: str = "soa_show_epochs"
    study_field_soa_show_milestones: str = "soa_show_milestones"
    study_field_soa_baseline_as_time_zero: str = "baseline_as_time_zero"
    study_soa_preferences_fields: tuple[str, str, str] = (
        # can't be a set: Neomodel's transform_operator_to_filter is strict for IN operator only accepts list or tuple
        study_field_soa_show_epochs,
        study_field_soa_show_milestones,
        study_field_soa_baseline_as_time_zero,
    )

    study_visit_contact_mode_name: str = "Visit Contact Mode"
    study_visit_epoch_allocation_name: str = "Epoch Allocation"
    date_time_format: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    operator_parameter_name: str = "Operator"

    day_unit_name: str = "day"
    days_unit_name: str = "days"
    # conversion to second which is master unit for time units
    day_unit_conversion_factor_to_master: int = 86400
    week_unit_name: str = "week"
    # conversion to second which is master unit for time units
    week_unit_conversion_factor_to_master: int = 604800
    study_time_unit_subset: str = "Study Time"

    default_study_field_config_file: str = (
        "clinical_mdr_api/tests/data/study_fields_modified.csv"
    )

    library_substances_codelist_name: str = "UNII"

    sponsor_model_prefix: str = "mastermodel"
    sponsor_model_version_number_prefix: str = "NN"

    # endregion


settings = Settings()  # type: ignore[call-arg]

# Teach urljoin that Neo4j DSN URLs like bolt:// and neo4j:// semantically similar to http://
for scheme in ("bolt", "bolt+s", "neo4j", "neo4j+s"):
    urllib.parse.uses_relative.append(scheme)
    urllib.parse.uses_netloc.append(scheme)

neomodel_config.DATABASE_URL = settings.neo4j_dsn
if settings.neo4j_database:
    neomodel_config.DATABASE_URL = urllib.parse.urljoin(
        settings.neo4j_dsn, f"/{settings.neo4j_database}"
    )

neomodel_config.MAX_CONNECTION_LIFETIME = settings.neo4j_connection_lifetime
