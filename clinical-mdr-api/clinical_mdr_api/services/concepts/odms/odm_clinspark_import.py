from typing import Any

from fastapi import UploadFile

from clinical_mdr_api.models.concepts.odms.odm_form import OdmFormPostInput
from clinical_mdr_api.models.concepts.odms.odm_item import (
    OdmItemPostInput,
    OdmItemTermRelationshipInput,
    OdmItemUnitDefinitionRelationshipInput,
)
from clinical_mdr_api.models.concepts.odms.odm_item_group import OdmItemGroupPostInput
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import (
    CTCodelistCreateInput,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributes,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import CTTermCreateInput
from clinical_mdr_api.services.concepts.odms.odm_xml_importer import (
    OdmXmlImporterService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_attributes import (
    CTCodelistAttributesService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist_name import (
    CTCodelistNameService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.controlled_terminologies.ct_term_name import (
    CTTermNameService,
)
from common import exceptions


class OdmClinicalXmlImporterService(OdmXmlImporterService):
    ct_term_name_service: CTTermNameService
    ct_codelist_attributes_service: CTCodelistAttributesService
    ct_codelist_name_service: CTCodelistNameService
    ct_codelist_service: CTCodelistService
    ct_term_service: CTTermService

    db_ct_codelist_attributes: list[CTCodelistAttributes]

    def __init__(self, xml_file: UploadFile, mapper_file: UploadFile | None):
        self.ct_term_name_service = CTTermNameService()
        self.ct_codelist_attributes_service = CTCodelistAttributesService()
        self.ct_codelist_name_service = CTCodelistNameService()
        self.ct_codelist_service = CTCodelistService()
        self.ct_term_service = CTTermService()

        self.db_ct_codelist_attributes = []
        self.unit_definition_uids_by: dict[str, str] = {}
        self.measurement_unit_names_by_oid = {}

        super().__init__(xml_file, mapper_file)

    def store_odm_xml(self):
        self._set_unit_definitions()
        self._set_unit_definition_uids_by()
        self._set_measurement_unit_names_by_oid()
        self._set_codelists()

        return super().store_odm_xml()

    def _set_unit_definitions(self):
        measurement_unit_names = {
            measurement_unit.getAttribute("Name")
            for measurement_unit in self.measurement_units
        }

        rs, _ = self._repos.unit_definition_repository.find_all(
            filter_by={"name": {"v": measurement_unit_names, "op": "eq"}},
        )

        rs_names = {item.name for item in rs}

        non_existent_measurement_unit_names = measurement_unit_names - rs_names

        exceptions.BusinessLogicException.raise_if(
            non_existent_measurement_unit_names,
            msg=f"MeasurementUnits with Names '{non_existent_measurement_unit_names}' don't match any Unit Definition.",
        )

        self.db_unit_definitions = [
            UnitDefinitionModel.from_unit_definition_ar(
                unit_definition_ar,
                find_term_by_uid=self._repos.ct_term_name_repository.find_by_uid,
                find_dictionary_term_by_uid=self._repos.dictionary_term_generic_repository.find_by_uid,
            )
            for unit_definition_ar in rs
        ]

    def _set_unit_definition_uids_by(self):
        self.unit_definition_uids_by = {
            db_unit_definition.name: db_unit_definition.uid
            for db_unit_definition in self.db_unit_definitions
        }

    def _set_measurement_unit_names_by_oid(self):
        self.measurement_unit_names_by_oid = {
            measurement_unit.getAttribute("OID"): measurement_unit.getAttribute("Name")
            for measurement_unit in self.measurement_units
        }

    def _set_codelists(self):
        rs = self._get_and_create_codelists()

        self.db_ct_codelist_attributes = [
            self.ct_codelist_attributes_service._transform_aggregate_root_to_pydantic_model(
                item_ar
            )
            for item_ar in rs
        ]

    def _set_ct_term_attributes(self):
        term_attributes = self._get_and_create_term_attributes()

        self.db_ct_term_attributes = [
            self.ct_term_attributes_service._transform_aggregate_root_to_pydantic_model(
                item_ar
            )
            for item_ar in term_attributes
        ]

    def _get_and_create_codelists(self):
        rs = self._repos.ct_codelist_attribute_repository.find_all(
            filter_by={
                "submission_value": {
                    "v": [
                        self._get_codelist_description_translatedtext_value(codelist)
                        for codelist in self.codelists
                    ],
                    "op": "eq",
                }
            }
        ).items
        existing_codelist_submission_values = {
            elm.ct_codelist_vo.submission_value for elm in rs
        }

        new_codelist_uids = set()
        for codelist in self.codelists:
            submission_value = self._get_codelist_description_translatedtext_value(
                codelist
            )

            if submission_value not in existing_codelist_submission_values:
                ct_codelist = self.ct_codelist_service.non_transactional_create(
                    CTCodelistCreateInput(
                        catalogue_name="CDASH CT",
                        name=codelist.getAttribute("Name"),
                        submission_value=submission_value,
                        nci_preferred_name=codelist.getAttribute("Name"),
                        definition=codelist.getAttribute("Name"),
                        sponsor_preferred_name=codelist.getAttribute("Name"),
                        extensible=True,
                        template_parameter=True,
                        parent_codelist_uid=None,
                        library_name="Sponsor",
                        terms=[],
                    )
                )
                self.ct_codelist_name_service.non_transactional_approve(
                    ct_codelist.codelist_uid
                )
                self.ct_codelist_attributes_service.non_transactional_approve(
                    ct_codelist.codelist_uid
                )
                new_codelist_uids.add(ct_codelist.codelist_uid)
                existing_codelist_submission_values.add(submission_value)

        if new_codelist_uids:
            rs.extend(
                self._repos.ct_codelist_attribute_repository.find_all(
                    filter_by={"codelist_uid": {"v": new_codelist_uids, "op": "eq"}}
                ).items
            )

        return rs

    def _get_and_create_term_attributes(self):
        def manage_codelist_item():
            if (
                codelist_item.getAttribute("CodedValue")
                not in term_code_submission_values
                and active_codelist.codelist_uid is not None
            ):
                ct_term = self.ct_term_service.non_transactional_create(
                    CTTermCreateInput(
                        catalogue_name="CDASH CT",
                        codelist_uid=active_codelist.codelist_uid,
                        code_submission_value=codelist_item.getAttribute("CodedValue"),
                        name_submission_value=codelist_item.getAttribute("CodedValue"),
                        nci_preferred_name=translated_txt,
                        definition=translated_txt,
                        sponsor_preferred_name=translated_txt,
                        sponsor_preferred_name_sentence_case=translated_txt.lower(),
                        library_name="Sponsor",
                        order=999999,
                    )
                )
                self.ct_term_name_service.non_transactional_approve(ct_term.term_uid)
                self.ct_term_attributes_service.non_transactional_approve(
                    ct_term.term_uid
                )
                term_attribute_uids.add(ct_term.term_uid)
                term_code_submission_values.add(ct_term.code_submission_value)
                return True

            for item in rs.items:
                if (
                    codelist_item.getAttribute("CodedValue")
                    != item.ct_term_vo.code_submission_value
                    or item.ct_term_vo.codelists[0].codelist_uid
                    != active_codelist.codelist_uid
                ):
                    continue

                if active_codelist.codelist_uid in term_codelist_uids:
                    term_attribute_uids.add(item.uid)
                    return True

                self.ct_codelist_service.non_transactional_add_term(
                    active_codelist.codelist_uid,
                    item.uid,
                    idx,
                )
                term_attribute_uids.add(item.uid)
                return True

            return False

        rs = self._repos.ct_term_attributes_repository.find_all(
            filter_by={
                "code_submission_value": {
                    "v": [
                        codelist_item.getAttribute("CodedValue")
                        for codelist in self.codelists
                        for codelist_item in codelist.getElementsByTagName(
                            "CodeListItem"
                        )
                    ],
                    "op": "eq",
                }
            }
        )
        term_codelist_uids = {
            codelist.codelist_uid
            for item in rs.items
            for codelist in item.ct_term_vo.codelists
        }
        term_code_submission_values = {
            item.ct_term_vo.code_submission_value for item in rs.items
        }

        term_attribute_uids: set[str] = set()
        for codelist in self.codelists:
            try:
                active_codelist = next(
                    db_ct_codelist_attribute
                    for db_ct_codelist_attribute in self.db_ct_codelist_attributes
                    if self._get_codelist_description_translatedtext_value(codelist)
                    == db_ct_codelist_attribute.submission_value
                )
            except StopIteration as exc:
                raise exceptions.NotFoundException(
                    "Codelist", codelist.getAttribute("OID"), "OID"
                ) from exc

            for idx, codelist_item in enumerate(
                codelist.getElementsByTagName("CodeListItem")
            ):
                translated_txt: str = (
                    codelist_item.getElementsByTagName("Decode")[0]
                    .getElementsByTagName("TranslatedText")[0]
                    .firstChild.nodeValue
                )

                if manage_codelist_item():
                    continue

        return self._repos.ct_term_attributes_repository.find_all(
            filter_by={"term_uid": {"v": term_attribute_uids, "op": "eq"}}
        ).items

    def _get_item_unit_definition_inputs(self, item_def):
        try:
            return [
                OdmItemUnitDefinitionRelationshipInput(
                    uid=self.unit_definition_uids_by[
                        self.measurement_unit_names_by_oid[
                            measurement_unit_ref.getAttribute("MeasurementUnitOID")
                        ]
                    ]
                )
                for measurement_unit_ref in item_def.getElementsByTagName(
                    "MeasurementUnitRef"
                )
            ]
        except KeyError as exc:
            raise exceptions.BusinessLogicException(
                msg=f"MeasurementUnit with OID '{exc}' was not provided."
            )

    def _get_odm_item_post_input(self, item_def):
        descriptions = self._extract_descriptions(item_def)

        plausible_duplicates = self.odm_item_service.non_transactional_get_all_concepts(
            filter_by={"name": {"v": [item_def.getAttribute("Name")], "op": "co"}}
        ).items

        item_unit_definitions = self._get_item_unit_definition_inputs(item_def)

        codelist = next(
            (
                codelist
                for codelist in self.codelists
                if item_def.getElementsByTagName("CodeListRef")
                and codelist.getAttribute("OID")
                == item_def.getElementsByTagName("CodeListRef")[0].getAttribute(
                    "CodeListOID"
                )
            ),
            None,
        )

        codelist_uid = next(
            (
                db_ct_codelist_attribute.codelist_uid
                for db_ct_codelist_attribute in self.db_ct_codelist_attributes
                if codelist
                and self._get_codelist_description_translatedtext_value(codelist)
                == db_ct_codelist_attribute.submission_value
            ),
            None,
        )

        input_terms = []
        if codelist:
            term_uid_map = {
                (
                    db_ct_term_attribute.codelists[0].codelist_uid,
                    db_ct_term_attribute.code_submission_value,
                ): db_ct_term_attribute.term_uid
                for db_ct_term_attribute in self.db_ct_term_attributes
            }

            for codelist_item in codelist.getElementsByTagName("CodeListItem"):
                key = (
                    str(codelist_uid) if codelist_uid is not None else "",
                    codelist_item.getAttribute("CodedValue"),
                )
                term_uid = term_uid_map.get(key, None)
                if key in term_uid_map and term_uid:
                    input_terms.append(
                        OdmItemTermRelationshipInput(
                            uid=term_uid,
                            order=int(float(codelist_item.getAttribute("Rank") or "1")),
                            display_text=codelist_item.getElementsByTagName(
                                "TranslatedText"
                            )[0].firstChild.nodeValue,
                        )
                    )

        return (
            OdmItemPostInput(
                oid=item_def.getAttribute("OID"),
                name=self.get_next_available_name(
                    item_def.getAttribute("Name"), plausible_duplicates
                ),
                prompt=item_def.getAttribute("Prompt"),
                datatype=item_def.getAttribute("DataType"),
                length=item_def.getAttribute("Length") or None,
                significant_digits=item_def.getAttribute("SignificantDigits") or None,
                sas_field_name=item_def.getAttribute("SASFieldName"),
                sds_var_name=item_def.getAttribute("SDSVarName"),
                origin=item_def.getAttribute("Origin"),
                comment=None,
                descriptions=[
                    self._create_description(
                        name=description["name"],
                        description=description["description"],
                        lang=description["lang"],
                    ).uid
                    for description in descriptions
                ],
                alias_uids=[],
                unit_definitions=item_unit_definitions,
                codelist_uid=codelist_uid,
                terms=input_terms,
            ),
            input_terms,
            item_unit_definitions,
        )

    def _get_odm_item_group_post_input(self, item_group_def):
        descriptions = self._extract_descriptions(item_group_def)

        plausible_duplicates = (
            self.odm_item_group_service.non_transactional_get_all_concepts(
                filter_by={
                    "name": {"v": [item_group_def.getAttribute("Name")], "op": "co"}
                }
            ).items
        )

        return OdmItemGroupPostInput(
            oid=item_group_def.getAttribute("OID"),
            name=self.get_next_available_name(
                item_group_def.getAttribute("Name"), plausible_duplicates
            ),
            origin=item_group_def.getAttribute("Origin"),
            repeating=item_group_def.getAttribute("Repeating"),
            is_reference_data="no",  # missing in odm
            purpose=item_group_def.getAttribute("Purpose"),
            sas_dataset_name=item_group_def.getAttribute("SASDatasetName"),
            comment=None,
            descriptions=[
                self._create_description(
                    name=description["name"],
                    description=description["description"],
                    lang=description["lang"],
                ).uid
                for description in descriptions
            ],
            alias_uids=[],
            sdtm_domain_uids=[],
        )

    def _get_odm_form_post_input(self, form_def):
        descriptions = self._extract_descriptions(form_def)

        plausible_duplicates = self.odm_form_service.non_transactional_get_all_concepts(
            filter_by={"name": {"v": [form_def.getAttribute("Name")], "op": "co"}}
        ).items

        return OdmFormPostInput(
            oid=form_def.getAttribute("OID"),
            name=self.get_next_available_name(
                form_def.getAttribute("Name"), plausible_duplicates
            ),
            sdtm_version="",
            repeating=form_def.getAttribute("Repeating"),
            scope_uid=None,
            descriptions=[
                self._create_description(
                    name=description["name"],
                    description=description["description"],
                    lang=description["lang"],
                ).uid
                for description in descriptions
            ],
            alias_uids=[],
        )

    @staticmethod
    def get_next_available_name(name: str, objs: list[Any]):
        duplicates = []
        for obj in objs:
            before, _, after = obj.name.partition(name)
            if not before and after.strip().isdigit():
                duplicates.append(obj)

        duplicates.sort(key=lambda x: x.name)

        if duplicates:
            _, _, number = duplicates[-1].name.rpartition(" ")

            if not number.isdigit():
                return name + " 1"

            return name + f" {int(number) + 1}"

        return name + " 1"
