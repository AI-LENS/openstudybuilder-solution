import asyncio
import csv
from datetime import datetime
import json
import os
import re
from collections import defaultdict

import aiohttp

from importers.functions.caselessdict import CaselessDict
from importers.functions.utils import load_env
from importers.utils.importer import BaseImporter, open_file_async
from importers.utils.metrics import Metrics

# ---------------------------------------------------------------
# Env loading
# ---------------------------------------------------------------
#
SAMPLE = load_env("MDR_MIGRATION_SAMPLE", default="False") == "True"
API_BASE_URL = load_env("API_BASE_URL")

MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS = load_env(
    "MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS"
)
MDR_MIGRATION_ACTIVITY_ITEM_CLASS_MODEL_RELS = load_env(
    "MDR_MIGRATION_ACTIVITY_ITEM_CLASS_MODEL_RELS"
)
MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY"
)
MDR_MIGRATION_SPONSOR_MODEL_DATASETS = load_env("MDR_MIGRATION_SPONSOR_MODEL_DATASETS")
MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES"
)
MDR_MIGRATION_SPONSOR_MODEL_WRITE_LOGFILE = load_env(
    "MDR_MIGRATION_SPONSOR_MODEL_WRITE_LOGFILE"
)

SPONSOR_MODELS_PATH_PREFIX = "/standards/sponsor-models/"
SPONSOR_MODELS_PATH = SPONSOR_MODELS_PATH_PREFIX + "models"
SPONSOR_MODELS_DATASETS_PATH = SPONSOR_MODELS_PATH_PREFIX + "datasets"
SPONSOR_MODELS_DATASET_VARIABLES_PATH = SPONSOR_MODELS_PATH_PREFIX + "dataset-variables"
ACTIVITY_INSTANCE_CLASSES_PATH = "/activity-instance-classes"
ACTIVITY_ITEM_CLASSES_PATH = "/activity-item-classes"


# SponsorModels with datasets and variables
class SponsorModels(BaseImporter):
    logging_name = "sponsor_models"

    def __init__(self, api=None, metrics_inst=None, cache=None):
        super().__init__(api=api, metrics_inst=metrics_inst, cache=cache)

        self._common_body_params = {}
        self._model_body_params = {}
        self.logfile_name = (
            f"sponsor_model_import_issues_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.txt"
            if MDR_MIGRATION_SPONSOR_MODEL_WRITE_LOGFILE
            else None
        )

    def parse_bool(self, cell: str | None) -> bool | None:
        if cell is None:
            return None
        else:
            return cell in ["Y", "X"]

    def reverse_bool(self, boolean: bool | None) -> bool | None:
        if boolean is None:
            return None
        else:
            return False if boolean else True

    def parse_instance_class_name(self, name: str) -> str:
        parsed = name.replace("AP ", "AssociatedPersons")
        return parsed

    def parse_item_class_name(self, name: str) -> str:
        return name.replace(" ", "").lower()

    def parse_variable_class_name(self, name: str) -> str:
        return name.replace("__", "--")

    @open_file_async()
    async def handle_activity_instance_class_relations(
        self, instance_class_csvfile, session
    ):
        api_tasks = []

        # Parse and PATCH ActivityInstanceClasses
        csv_reader = csv.reader(instance_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_instance_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_INSTANCE_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_instance_classes = {
            self.parse_instance_class_name(i): v
            for i, v in existing_instance_classes.items()
        }

        grouped_items = {}

        for row in csv_reader:
            class_cell = row[headers.index("activity_instance_class")]
            if class_cell:
                activity_instance_class_uid = existing_instance_classes.get(
                    self.parse_instance_class_name(class_cell),
                    None,
                )
                if activity_instance_class_uid is not None:
                    grouped_items[activity_instance_class_uid] = row[
                        headers.index("dataset_class")
                    ]

        for instance_class_uid, dataset in grouped_items.items():
            data = {
                "body": {
                    "dataset_class_uid": dataset,
                },
            }
            self.log.info(
                "Adding relationship to dataset for activity instance class '%s'",
                instance_class_uid,
            )
            api_tasks.append(
                self.api.patch_to_api_async(
                    path=f"{ACTIVITY_INSTANCE_CLASSES_PATH}/{instance_class_uid}/model-mappings",
                    body=data["body"],
                    session=session,
                )
            )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    @open_file_async()
    async def handle_activity_item_class_relations(self, item_class_csvfile, session):
        api_tasks = []

        # Parse and PATCH ActivityItemClasses
        csv_reader = csv.reader(item_class_csvfile, delimiter=",")
        headers = next(csv_reader)
        existing_item_classes = self.api.get_all_identifiers(
            self.api.get_all_from_api(ACTIVITY_ITEM_CLASSES_PATH),
            identifier="name",
            value="uid",
        )

        existing_item_classes = {
            self.parse_item_class_name(i): v for i, v in existing_item_classes.items()
        }

        grouped_items = defaultdict(list)

        for row in csv_reader:
            class_cell = row[headers.index("activity_item_class")]
            if class_cell:
                activity_item_class_uid = existing_item_classes.get(
                    self.parse_item_class_name(class_cell),
                    None,
                )
                if activity_item_class_uid is not None:
                    variable_class_uid = self.parse_variable_class_name(
                        row[headers.index("variable_class")]
                    )
                    # There are some duplicates in the CSV file
                    if variable_class_uid not in grouped_items[activity_item_class_uid]:
                        grouped_items[activity_item_class_uid].append(
                            variable_class_uid
                        )

        for item_class_uid, variables in grouped_items.items():
            data = {
                "body": {
                    "variable_class_uids": variables,
                },
            }
            self.log.info(
                "Adding relationships to variables for activity item class '%s'",
                item_class_uid,
            )
            api_tasks.append(
                self.api.patch_to_api_async(
                    path=f"{ACTIVITY_ITEM_CLASSES_PATH}/{item_class_uid}/model-mappings",
                    body=data["body"],
                    session=session,
                )
            )

        # Finally, push all tasks
        await asyncio.gather(*api_tasks)

    async def handle_sponsor_model(self, session) -> bool:
        existing_sponsor_models = self.api.get_all_identifiers(
            self.api.get_all_from_api(SPONSOR_MODELS_PATH),
            identifier="name",
            value="uid",
        )

        sponsor_model_name = self._common_body_params["sponsor_model_name"]
        if sponsor_model_name in existing_sponsor_models:
            self.log.info(
                f"Sponsor model version {sponsor_model_name} already exists in database. Skipping import."
            )
            return False

        api_tasks = []

        data = {
            "body": self._model_body_params,
        }
        self.log.info(
            f"Add sponsor model for Implementation Guide '{data['body']['ig_uid']}' version '{data['body']['ig_version_number']}'"
        )

        api_tasks.append(
            self.api.post_to_api_async(
                url=SPONSOR_MODELS_PATH,
                body=data["body"],
                session=session,
                logfile_name=self.logfile_name,
            )
        )
        await asyncio.gather(*api_tasks)

        return True

    def parse_dataset_class_name(
        self, class_name: str, dataset_name: str | None = None
    ) -> str:
        # First, remove prefixes like AP
        class_name = class_name.replace("AP ", "")

        # In case the class_name passed is "CO" or "DM" or similar
        # Then it should become "Special-Purpose-CO" - see below
        if dataset_name is None:
            if len(class_name) == 2:
                dataset_name = class_name
                class_name = "Special-Purpose"

        # Sentence case
        class_name = class_name.title()

        # Switch some special names
        if class_name in ["Identifiers", "Timing"]:
            class_name = "General Observations"

        # Transform spaces
        # But first, "Special Purpose" needs a dash
        if "Special Purpose" in class_name:
            class_name = "Special-Purpose"
        class_name = class_name.replace(" ", "__")

        # Treat classes that require su ffix with dataset name
        # For example, "APDM" -> "Special-Purpose-DM"
        if class_name in [
            "Relationship",
            "Special-Purpose",
            "Study__Reference",
            "Trial__Design",
        ]:
            dataset_name = (
                dataset_name.replace("AP", "")
                if dataset_name.startswith("AP")
                else dataset_name
            )
            class_name = f"{class_name}-{dataset_name}"

        return class_name

    @open_file_async()
    async def handle_datasets(self, csvfile, session):
        # Populate sponsor model datasets
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        for row in csv_reader:
            data = {
                "body": {
                    # Expected fields
                    "dataset_uid": row[headers.index("Table")],
                    "implemented_dataset_class": self.parse_dataset_class_name(
                        row[headers.index("Class")], row[headers.index("Table")]
                    ),
                    "enrich_build_order": (
                        row[headers.index("enrich_build_order")]
                        if row[headers.index("enrich_build_order")]
                        else 0
                    ),
                    # Optional/Changeable fields
                    # Update in the API if renamed or new fields are added
                    "is_basic_std": self.parse_bool(row[headers.index("basic_std")]),
                    "label": row[headers.index("Label")],
                    "xml_path": row[headers.index("XmlPath")],
                    "xml_title": row[headers.index("XmlTitle")],
                    "structure": row[headers.index("Structure")],
                    "purpose": row[headers.index("Purpose")],
                    "keys": (
                        row[headers.index("Keys")].split(" ")
                        if row[headers.index("Keys")]
                        else None
                    ),
                    "sort_keys": (
                        row[headers.index("SortKeys")].split(" ")
                        if row[headers.index("SortKeys")]
                        else None
                    ),
                    "state": row[headers.index("State")],
                    "is_cdisc_std": (
                        self.reverse_bool(
                            self.parse_bool(row[headers.index("isnotcdiscstd")])
                        )
                        if "isnotcdiscstd" in headers
                        else self.parse_bool(row[headers.index("basic_std")])
                    ),
                    "source_ig": (
                        row[headers.index("cdiscstd")]
                        if "cdiscstd" in headers
                        else None
                    ),
                    "standard_ref": row[headers.index("Standardref")] or None,
                    "comment": row[headers.index("comment")] or None,
                    "ig_comment": row[headers.index("IGcomment")],
                    "map_domain_flag": self.parse_bool(
                        row[headers.index("map_domain_flag")]
                    ),
                    "suppl_qual_flag": self.parse_bool(
                        row[headers.index("suppl_qual_flag")]
                    ),
                    "include_in_raw": self.parse_bool(
                        row[headers.index("include_in_raw")]
                    ),
                    "gen_raw_seqno_flag": self.parse_bool(
                        row[headers.index("gen_raw_seqno_flag")]
                    ),
                    "extended_domain": row[headers.index("extended_domain")],
                    **self._common_body_params,
                },
            }
            self.log.info(
                f"Add sponsor model dataset '{data['body']['dataset_uid']}' to sponsor model '{data['body']['sponsor_model_name']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_DATASETS_PATH,
                    body=data["body"],
                    session=session,
                    logfile_name=self.logfile_name,
                )
            )

            # If relevant, add a sponsor term to the Domain codelist
            if data["body"]["is_basic_std"] is False:
                term_data = {
                    "body": {
                        "catalogue_name": "SDTM CT",
                        "codelist_uid": "C66734",
                        "code_submission_value": data["body"]["dataset_uid"],
                        "name_submission_value": data["body"]["label"],
                        "nci_preferred_name": "UNK",
                        "definition": data["body"]["comment"],
                        "sponsor_preferred_name": data["body"]["label"],
                        "sponsor_preferred_name_sentence_case": data["body"][
                            "label"
                        ].lower(),
                        "order": data["body"]["enrich_build_order"],
                        "library_name": "Sponsor",
                    },
                }
                api_tasks.append(
                    self.api.post_to_api_async(
                        url="/ct/terms",
                        body=term_data["body"],
                        session=session,
                        logfile_name=self.logfile_name,
                    )
                )

        await asyncio.gather(*api_tasks)

    # Get all terms from a codelist
    def _get_codelist_terms(self, codelist_uid):
        self.ensure_cache()
        if codelist_uid is not None:
            terms = [
                term
                for term in self.cache.all_terms_attributes
                if codelist_uid in [x["codelist_uid"] for x in term["codelists"]]
            ]
            return terms

    # Get a dictionary mapping submission values to term uids for a codelist identified by its uid
    def _get_submissionvalues_for_codelist(self, codelist_uid):
        terms = self._get_codelist_terms(codelist_uid)
        name_submvals = CaselessDict(
            self.api.get_all_identifiers(
                terms,
                identifier="name_submission_value",
                value="term_uid",
            )
        )
        code_submvals = CaselessDict(
            self.api.get_all_identifiers(
                terms,
                identifier="code_submission_value",
                value="term_uid",
            )
        )
        name_submvals.update(code_submvals)
        return name_submvals

    def parse_referenced_ct(self, headers, row, all_codelist_uids) -> tuple[dict, dict]:
        # Sponsor specific code
        # Custom logic to extract CT relationships at sponsor model level
        references_codelists = []
        references_terms = []
        xml_codelist_multi = self.parse_bool(row[headers.index("xmlcodelist_multi")])
        term = row[headers.index("term")] or None
        # Some Variables link to multiple codelists
        if xml_codelist_multi is True and term != "*":
            for submval in row[headers.index("term")].split("|"):
                submval = re.sub(r"[()]", "", submval)
                if submval in all_codelist_uids:
                    references_codelists.append(all_codelist_uids.get(submval))
        # All others link to a single one
        else:
            _codelist_uid = all_codelist_uids.get(row[headers.index("xmlcodelist")])
            if _codelist_uid:
                references_codelists.append(_codelist_uid)

                # Variables referencing a single codelist can reference specific Terms too
                # As a subset of the referenced codelist
                if row[headers.index("xmlcodelistvalues")]:
                    terms_in_codelist = self._get_submissionvalues_for_codelist(
                        _codelist_uid
                    )
                    for term_submval in row[headers.index("xmlcodelistvalues")].split(
                        "|"
                    ):
                        # Known special case
                        if term_submval == "U":
                            term_submval = "UNKNOWN"
                        if term_submval in terms_in_codelist:
                            references_terms.append(terms_in_codelist[term_submval])
        return references_codelists, references_terms

    @open_file_async()
    async def handle_dataset_variables(self, csvfile, session):
        # Populate sponsor model dataset variables
        csv_reader = csv.reader(csvfile, delimiter=",")
        headers = next(csv_reader)
        api_tasks = []

        all_codelist_uids = self.api.get_codelists_uid_and_submval()

        for row in csv_reader:
            references_codelists, references_terms = self.parse_referenced_ct(
                headers=headers, row=row, all_codelist_uids=all_codelist_uids
            )
            data = {
                "body": {
                    # Expected fields
                    "dataset_uid": row[headers.index("table")],
                    "dataset_variable_uid": row[headers.index("column")],
                    "implemented_parent_dataset_class": self.parse_dataset_class_name(
                        class_name=row[headers.index("class_table")],
                    ),
                    "implemented_variable_class": self.parse_variable_class_name(
                        row[headers.index("class_column")]
                    ),
                    "order": row[headers.index("order")],
                    # Optional/Changeable fields
                    # Update in the API if renamed or new fields are added
                    "is_basic_std": self.parse_bool(row[headers.index("basic_std")]),
                    "label": row[headers.index("label")],
                    "variable_type": row[headers.index("type")],
                    "length": row[headers.index("length")],
                    "display_format": row[headers.index("displayformat")] or None,
                    "xml_datatype": row[headers.index("xmldatatype")],
                    "references_codelists": references_codelists,
                    "references_terms": references_terms,
                    "core": row[headers.index("core")],
                    "origin": row[headers.index("origin")] or None,
                    "origin_type": (
                        row[headers.index("origintype")] or None
                        if "origintype" in headers
                        else None
                    ),
                    "origin_source": (
                        row[headers.index("originsource")] or None
                        if "originsource" in headers
                        else None
                    ),
                    "role": row[headers.index("role")],
                    "term": row[headers.index("term")] or None,
                    "algorithm": row[headers.index("algorithm")] or None,
                    "qualifiers": (
                        row[headers.index("qualifiers")].split(" ") or None
                        if row[headers.index("qualifiers")]
                        else None
                    ),
                    "is_cdisc_std": (
                        self.reverse_bool(
                            self.parse_bool(row[headers.index("isnotcdiscstd")])
                        )
                        if "isnotcdiscstd" in headers
                        else self.parse_bool(row[headers.index("basic_std")])
                    ),
                    "comment": row[headers.index("comment")] or None,
                    "ig_comment": row[headers.index("IGcomment")] or None,
                    "map_var_flag": row[headers.index("map_var_flag")],
                    "fixed_mapping": row[headers.index("fixed_mapping")] or None,
                    "include_in_raw": self.parse_bool(
                        row[headers.index("include_in_raw")]
                    ),
                    "nn_internal": self.parse_bool(row[headers.index("nn_internal")]),
                    "value_lvl_where_cols": row[headers.index("value_lvl_where_cols")]
                    or None,
                    "value_lvl_label_col": row[headers.index("value_lvl_label_col")]
                    or None,
                    "value_lvl_collect_ct_val": row[
                        headers.index("value_lvl_collect_ct_val")
                    ]
                    or None,
                    "value_lvl_ct_codelist_id_col": row[
                        headers.index("value_lvl_ct_cdlist_id_col")
                    ]
                    or None,
                    "enrich_build_order": (
                        row[headers.index("enrich_build_order")] or None
                        if row[headers.index("enrich_build_order")]
                        else 0
                    ),
                    "enrich_rule": row[headers.index("enrich_rule")] or None,
                    **self._common_body_params,
                },
            }
            self.log.info(
                f"Add sponsor model variable '{data['body']['dataset_variable_uid']}' to dataset '{data['body']['dataset_uid']}'"
            )
            api_tasks.append(
                self.api.post_to_api_async(
                    url=SPONSOR_MODELS_DATASET_VARIABLES_PATH,
                    body=data["body"],
                    session=session,
                    logfile_name=self.logfile_name,
                )
            )
        await asyncio.gather(*api_tasks)

    async def async_run(self):
        timeout = aiohttp.ClientTimeout(None)
        conn = aiohttp.TCPConnector(limit=4, force_close=True)
        async with aiohttp.ClientSession(timeout=timeout, connector=conn) as session:
            await self.handle_activity_instance_class_relations(
                MDR_MIGRATION_ACTIVITY_INSTANCE_CLASS_MODEL_RELS,
                session,
            )
            await self.handle_activity_item_class_relations(
                MDR_MIGRATION_ACTIVITY_ITEM_CLASS_MODEL_RELS,
                session,
            )

            # For each subfolder in the sponsor models folder, import the corresponding sponsor model
            for root, dirs, _ in os.walk(MDR_MIGRATION_SPONSOR_MODEL_DIRECTORY):
                dirs.sort()
                for dir_name in dirs:
                    sponsor_model_path = os.path.join(root, dir_name)

                    # Open file model_info.json in directory
                    with open(os.path.join(sponsor_model_path, "model_info.json")) as f:
                        model_info = json.load(f)
                        if "exclude" in model_info and model_info["exclude"]:
                            self.log.info(
                                f"Skipping sponsor model '{model_info['sponsor_model_name']}'"
                            )
                            continue
                        self._common_body_params = {
                            "target_data_model_catalogue": model_info["ig_uid"],
                            "sponsor_model_name": model_info["sponsor_model_name"],
                            "sponsor_model_version_number": model_info[
                                "sponsor_model_version_number"
                            ],
                            "library_name": "Sponsor",
                        }

                        self._model_body_params = {
                            "ig_uid": model_info["ig_uid"],
                            "ig_version_number": model_info["ig_version_number"],
                            "version_number": model_info[
                                "sponsor_model_version_number"
                            ],
                            "library_name": "Sponsor",
                        }

                    continue_import = await self.handle_sponsor_model(session)
                    if continue_import:
                        await self.handle_datasets(
                            os.path.join(
                                sponsor_model_path, MDR_MIGRATION_SPONSOR_MODEL_DATASETS
                            ),
                            session,
                        )
                        await self.handle_dataset_variables(
                            os.path.join(
                                sponsor_model_path,
                                MDR_MIGRATION_SPONSOR_MODEL_DATASET_VARIABLES,
                            ),
                            session,
                        )

    def run(self):
        self.log.info("Importing sponsor models")

        # Create a file to log issues
        if self.logfile_name:
            with open(self.logfile_name, "w") as f:
                f.write("Sponsor Model Import Issues\n")

        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.async_run())
        self.log.info("Done importing sponsor models")


def main():
    metr = Metrics()
    migrator = SponsorModels(metrics_inst=metr)
    migrator.run()
    metr.print()


if __name__ == "__main__":
    main()
