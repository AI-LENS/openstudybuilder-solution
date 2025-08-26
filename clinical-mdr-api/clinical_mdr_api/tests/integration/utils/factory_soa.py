import logging
from collections import defaultdict
from typing import Any, Iterable

from clinical_mdr_api.domain_repositories.study_selections.study_soa_repository import (
    SoALayout,
)
from clinical_mdr_api.domains.controlled_terminologies.utils import TermParentType
from clinical_mdr_api.domains.study_selections.study_selection_base import SoAItemType
from clinical_mdr_api.domains.study_selections.study_visit import VisitGroupFormat
from clinical_mdr_api.models.concepts.activities.activity import Activity
from clinical_mdr_api.models.concepts.activities.activity_group import ActivityGroup
from clinical_mdr_api.models.concepts.activities.activity_instance import (
    ActivityInstance,
)
from clinical_mdr_api.models.concepts.activities.activity_sub_group import (
    ActivitySubGroup,
)
from clinical_mdr_api.models.concepts.unit_definitions.unit_definition import (
    UnitDefinitionModel,
)
from clinical_mdr_api.models.controlled_terminologies.ct_codelist import CTCodelist
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    CTTerm,
    CTTermNameAndAttributes,
)
from clinical_mdr_api.models.projects.project import Project
from clinical_mdr_api.models.study_selections.study import Study, StudySoaPreferences
from clinical_mdr_api.models.study_selections.study_epoch import StudyEpoch
from clinical_mdr_api.models.study_selections.study_selection import (
    ReferencedItem,
    StudyActivitySchedule,
    StudySelectionActivity,
    StudySelectionActivityInstance,
)
from clinical_mdr_api.models.study_selections.study_soa_footnote import StudySoAFootnote
from clinical_mdr_api.models.study_selections.study_visit import StudyVisit
from clinical_mdr_api.models.syntax_instances.footnote import Footnote
from clinical_mdr_api.models.syntax_templates.footnote_template import FootnoteTemplate
from clinical_mdr_api.repositories._utils import FilterOperator
from clinical_mdr_api.services.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassService,
)
from clinical_mdr_api.services.concepts.activities.activity_group_service import (
    ActivityGroupService,
)
from clinical_mdr_api.services.concepts.activities.activity_instance_service import (
    ActivityInstanceService,
)
from clinical_mdr_api.services.concepts.activities.activity_service import (
    ActivityService,
)
from clinical_mdr_api.services.concepts.activities.activity_sub_group_service import (
    ActivitySubGroupService,
)
from clinical_mdr_api.services.concepts.unit_definitions.unit_definition import (
    UnitDefinitionService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_codelist import (
    CTCodelistService,
)
from clinical_mdr_api.services.controlled_terminologies.ct_term import CTTermService
from clinical_mdr_api.services.studies.study_activity_instance_selection import (
    StudyActivityInstanceSelectionService,
)
from clinical_mdr_api.services.studies.study_flowchart import StudyFlowchartService
from clinical_mdr_api.services.studies.study_visit import StudyVisitService
from clinical_mdr_api.services.syntax_instances.footnotes import FootnoteService
from clinical_mdr_api.services.syntax_templates.footnote_templates import (
    FootnoteTemplateService,
)
from clinical_mdr_api.services.utils.table_f import TableWithFootnotes
from clinical_mdr_api.tests.integration.utils.utils import LIBRARY_NAME, TestUtils
from common import exceptions
from common.config import settings

log = logging.getLogger(__name__)


class SoATestData:
    database_name: str
    study: Study
    unit_definitions: dict[str, UnitDefinitionModel]
    _epoch_terms: dict[str, CTTerm]
    study_epochs: dict[str, StudyEpoch]
    _visit_type_terms: dict[str, CTTerm]
    _visit_contact_terms: dict[str, CTTerm]
    _visit_timeref_terms: dict[str, CTTerm]
    study_visits: dict[str, StudyVisit]
    _soa_group_terms: dict[str, CTTerm]
    activities: dict[str, Activity]
    _activity_groups: dict[str, ActivityGroup]
    _activity_subgroups: dict[str, ActivitySubGroup]
    _codelists: dict[str, CTCodelist]
    activity_instances: dict[str, dict[str, ActivityInstance]]
    study_activities: dict[str, StudySelectionActivity]
    study_activity_instances: dict[str, list[StudySelectionActivityInstance]]
    study_activity_schedules: list[StudyActivitySchedule]
    _footnote_types: dict[str, CTTerm]
    footnotes: dict[str, Footnote]
    soa_footnotes: list[StudySoAFootnote]
    soa_preferences: StudySoaPreferences

    EPOCHS = {
        "Screening": {"color_hash": "#80DEEAFF"},
        "Treatment": {"color_hash": "#C5E1A5FF"},
        "Follow-Up": {"color_hash": "#BCAAA4FF"},
    }
    VISITS = {
        "V1": {
            "epoch": "Screening",
            "type": "Screening",
            "visit_contact_mode": "On Site Visit",
            "is_global_anchor_visit": True,
            "day": 0,
            "min_window": -7,
            "max_window": 3,
        },
        "V2": {
            "epoch": "Treatment",
            "type": "Treatment",
            "visit_contact_mode": "On Site Visit",
            "day": 7,
            "min_window": -1,
            "max_window": 1,
        },
        "V3": {
            "epoch": "Treatment",
            "type": "Treatment",
            "visit_contact_mode": "On Site Visit",
            "day": 21,
            "min_window": -1,
            "max_window": 1,
        },
        "V4": {
            "epoch": "Follow-Up",
            "type": "Follow-Up",
            "visit_group": "V4-5",
            "visit_contact_mode": "On Site Visit",
            "day": 28,
            "min_window": -1,
            "max_window": 1,
        },
        "V5": {
            "epoch": "Follow-Up",
            "type": "Follow-Up",
            "visit_group": "V4-5",
            "visit_contact_mode": "On Site Visit",
            "day": 35,
            "min_window": -1,
            "max_window": 1,
        },
        "V6": {
            "epoch": "Follow-Up",
            "type": "Follow-Up",
            "visit_contact_mode": "Virtual Visit",
            "day": 49,
            "min_window": -3,
            "max_window": 3,
        },
    }
    NUM_VISIT_COLS = 5

    # Mind if an activity is scheduled for a visit of a visit-group, then it must be scheduled for all visits of the group.
    # Testing for safeguards on this is not in the scope of the tests of the SoA feature.
    ACTIVITIES = {
        "Randomized": {
            "soa_group": "Subject Related Information",
            "group": "Randomization",
            "subgroup": "Randomisation",
            "visits": ["V1"],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
            "instances": [
                {
                    "class": "Randomization class",
                    "name": "Randomized inst.",
                    "topic_code": "RANDTC",
                    "adam_param_code": "RADAM",
                }
            ],
        },
        "Weight": {
            "soa_group": "Subject Related Information",
            "group": "General",
            "subgroup": "Body Measurements",
            "visits": ["V1", "V3"],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
            "instances": [
                {
                    "class": "Weighting class",
                    "name": "Weight in kg",
                    "topic_code": "WEIGHTkg",
                    "adam_param_code": "Adam Heavy",
                },
                {
                    "class": "Weighting class",
                    "name": "Weight in stones",
                    "topic_code": "WEIGHTST",
                    "adam_param_code": "Lightadam",
                },
            ],
        },
        "I agree": {
            "soa_group": "Informed Consent",
            "library_name": settings.requested_library_name,
            "is_data_collected": True,
            "visits": ["V6"],
            "show_soa_group": True,
            "show_group": False,
            "show_subgroup": False,
            "show_activity": True,
        },
        "Eligibility Criteria Met": {
            "soa_group": "Subject Related Information",
            "group": "Eligibility Criteria",
            "subgroup": "Eligibility Criteria",
            "is_data_collected": False,
            "visits": [],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
            "instances": [
                {
                    "class": "Eligibility Class",
                    "name": "Subject is a human",
                    "topic_code": "HUMAN",
                    "adam_param_code": "HUM",
                },
                {
                    "class": "Eligibility Class",
                    "name": "Subject has one heart",
                    "topic_code": "ONEHEART",
                    "adam_param_code": "HEART1",
                },
            ],
        },
        "Parental Consent Obtained": {
            "soa_group": "Subject Related Information",
            "group": "Eligibility Criteria",
            "subgroup": None,
            "library_name": settings.requested_library_name,
            "is_data_collected": False,
            "visits": [],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": False,
            "show_activity": False,
        },
        "Systolic Blood Pressure": {
            "soa_group": "Safety",
            "group": "Vital Signs",
            "subgroup": "Vital Signs",
            "visits": ["V1", "V3", "V6"],
            "show_soa_group": True,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
        },
        "LDL Cholesterol": {
            "soa_group": "Subject Related Information",
            "group": "Laboratory Assessments",
            "subgroup": "Lipids",
            "visits": ["V1"],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": False,
            "show_activity": False,
        },
        "Mean glucose": {
            "soa_group": "Safety",
            "group": "General",
            "subgroup": "Self Measured Plasma glucose",
            "visits": ["V1", "V6"],
            "show_soa_group": True,
            "show_group": True,
            "show_subgroup": False,
            "show_activity": False,
        },
        "Creatine Kinase MM": {
            "soa_group": "Efficacy",
            "group": "Laboratory Assessments",
            "subgroup": "Biochemistry",
            "visits": [],
            "show_soa_group": False,
            "show_group": False,
            "show_subgroup": False,
            "show_activity": True,
        },
        "Cholesterol": {
            "soa_group": "Subject Related Information",
            "group": "Laboratory Assessments",
            "subgroup": "Lipids",
            "visits": ["V1", "V6"],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": False,
            "show_activity": True,
        },
        "Height": {
            "soa_group": "Subject Related Information",
            "group": "General",
            "subgroup": "Body Measurements",
            "visits": ["V1", "V2"],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
            "instances": [
                {
                    "class": "Height class",
                    "name": "Height cm",
                    "topic_code": "Heigh-cm",
                    "adam_param_code": "cmHeight",
                }
            ],
        },
        "Diastolic Blood Pressure": {
            "soa_group": "Safety",
            "group": "Vital Signs",
            "subgroup": "Vital Signs",
            "visits": ["V1", "V3", "V6"],
            "show_soa_group": True,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
        },
        "HbA1c": {
            "soa_group": "Efficacy",
            "group": "Laboratory Assessments",
            "subgroup": "Glucose Metabolism",
            "visits": ["V1", "V2", "V4", "V5", "V6"],
            "show_soa_group": False,
            "show_group": False,
            "show_subgroup": True,
            "show_activity": False,
        },
        "HDL Cholesterol": {
            "soa_group": "Subject Related Information",
            "group": "Laboratory Assessments",
            "subgroup": "Lipids",
            "visits": ["V4", "V5"],
            "show_soa_group": False,
            "show_group": True,
            "show_subgroup": False,
            "show_activity": False,
        },
        "Pulse Rate": {
            "soa_group": "Safety",
            "group": "Vital Signs",
            "subgroup": "Vital Signs",
            "visits": ["V2", "V4", "V5", "V6"],
            "show_soa_group": True,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": False,
            "instances": [
                {
                    "class": "Pulse class",
                    "name": "Pulse per minuate",
                    "topic_code": "pulman",
                    "adam_param_code": "ppm",
                },
                {
                    "class": "Pulse class",
                    "name": "Evaluation point",
                    "topic_code": "pulloc",
                    "adam_param_code": "pudl",
                },
            ],
        },
        "Over 18": {
            "soa_group": "Subject Related Information",
            "group": "Eligibility Criteria",
            "subgroup": "Other Eligibility Criteria",
            "library_name": settings.requested_library_name,
            "is_data_collected": False,
            "visits": [],
            "show_soa_group": False,
            "show_group": False,
            "show_subgroup": True,
            "show_activity": False,
        },
        "Albumin": {
            "soa_group": "Safety",
            "group": "AE Requiring Additional Data",
            "subgroup": "Laboratory Assessments",
            "visits": ["V2", "V3"],
            "show_soa_group": True,
            "show_group": False,
            "show_subgroup": False,
            "show_activity": False,
        },
    }
    NUM_SOA_ROWS = 43
    NUM_ACTIVITY_REQUEST_ROWS = 3 + 3 + 3  # 3 activity requests with their groupings
    NUM_ACTIVITY_INSTANCES = 8
    NUM_OPERATIONAL_SOA_ROWS = (
        NUM_SOA_ROWS - NUM_ACTIVITY_REQUEST_ROWS + NUM_ACTIVITY_INSTANCES
    )
    NUM_OPERATIONAL_SOA_SCHEDULES = 9  # Mind that study-activities are scheduled, not study-activity-instances, there may be multiple instances per activity
    NUM_OPERATIONAL_SOA_CHECKMARKS = (
        15  # Visits are no longer grouped in operational SoA
    )
    NUM_OPERATIONAL_SOA_EXPORT_ROWS = 15  # study-activity-instances ⋈ study-visits (one row per instance per visit the activity is scheduled to)

    FOOTNOTES = {
        "Dilution of hyperreal in ion-exchanged water applied orally": [],
        "Pharmacokinetic dance of molecules within the bloodstream": [
            {"type": SoAItemType.STUDY_VISIT.value, "name": "V4"},
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V2",
                "activity": "Pulse Rate",
            },
            {
                "type": SoAItemType.STUDY_ACTIVITY.value,
                "name": "Diastolic Blood Pressure",
            },
        ],
        "Pharmacological jigsaw puzzle assembles a mosaic of therapeutic agents to paint the canvas of wellness": [
            {"type": SoAItemType.STUDY_SOA_GROUP.value, "name": "Informed Consent"},
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V6",
                "activity": "Cholesterol",
            },
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V1",
                "activity": "Cholesterol",
            },
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V6",
                "activity": "I agree",
            },
            {"type": SoAItemType.STUDY_ACTIVITY_SUBGROUP.value, "name": "Lipids"},
            {
                "type": SoAItemType.STUDY_ACTIVITY.value,
                "name": "Parental Consent Obtained",
            },
            {"type": SoAItemType.STUDY_ACTIVITY_GROUP.value, "name": "General"},
        ],
        "In the desert of uncertainty, faith is the oasis": [],
        "The best way to predict your future is to create it": [
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V3",
                "activity": "Albumin",
            },
        ],
        "Therapeutic gold under the guidance of synthetic sorcery": [
            {"type": SoAItemType.STUDY_EPOCH.value, "name": "Treatment"},
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V5",
                "activity": "HDL Cholesterol",
            },
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V2",
                "activity": "Height",
            },
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V6",
                "activity": "I agree",
            },
            {"type": SoAItemType.STUDY_ACTIVITY_GROUP.value, "name": "Vital Signs"},
            {
                "type": SoAItemType.STUDY_ACTIVITY.value,
                "name": "Diastolic Blood Pressure",
            },
            {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "I agree"},
        ],
        "When the winds of change blow, only those who adjust their sails find their destined harbor.": [
            {"type": SoAItemType.STUDY_ACTIVITY.value, "name": "Albumin"},
        ],
    }

    AUTHOR_ID = "unknown-user"

    def __init__(self, project: Project):
        self.activities: dict[str, Activity] = {}
        self._activity_groups: dict[str, ActivityGroup] = {}
        self._activity_subgroups: dict[str, ActivitySubGroup] = {}
        self._codelists: dict[str, CTCodelist] = {}
        self.activity_instances = {}
        self.study_activities: dict[str, StudySelectionActivity] = {}
        self.study_activity_schedules: list[StudyActivitySchedule] = []

        self.study = TestUtils.create_study(
            number=TestUtils.random_str(4),
            project_number=project.project_number,
            description=f"Test study ({self.__class__.__name__})",
        )
        log.info("created study: [%s]", self.study.uid)

        TestUtils.set_study_standard_version(
            study_uid=self.study.uid, catalogue=settings.sdtm_ct_catalogue_name
        )

        # Study needs a title to be able to lock
        TestUtils.set_study_title(self.study.uid)

        self._unit_definitions = {
            u.name: u
            for u in UnitDefinitionService().get_all(library_name=LIBRARY_NAME).items
        }

        self._epoch_terms = self.create_epoch_terms()

        self.study_epochs = self.create_study_epochs(self.EPOCHS)

        self._visit_type_terms = self.create_codelist_with_terms(
            name=settings.study_visit_type_name,
            terms={
                "End of Treatment",
                "End of Trial",
                "Follow-Up",
                "Informed Consent",
                "No Treatment",
                "Non-Visit",
                "Randomisation",
                "Screening",
                "Treatment",
                "Unscheduled",
                "Washout",
            },
            sponsor_preferred_name=settings.study_visit_type_name,
            submission_value="TIMELB",
            extensible=True,
            approve=True,
        )

        self._visit_contact_terms = self.create_codelist_with_terms(
            name=settings.study_visit_contact_mode_name,
            terms={"On Site Visit", "Phone Contact", "Virtual Visit"},
            sponsor_preferred_name=settings.study_visit_contact_mode_name,
            submission_value="VISCNTMD",
            extensible=True,
            approve=True,
        )

        self._visit_timeref_terms = self.create_codelist_with_terms(
            name=settings.study_visit_timeref_name,
            terms={"BASELINE", "Global anchor visit", "BASELINE2"},
            sponsor_preferred_name=settings.study_visit_timeref_name,
            extensible=True,
            approve=True,
        )

        self.study_visits = self.create_study_visits(self.VISITS)

        self._soa_group_terms = self.create_codelist_with_terms(
            name="Flowchart Group",
            terms={
                "Informed Consent",
                "Eligibility And Other Criteria",
                "Subject Related Information",
                "Efficacy",
                "Safety",
                "Genetics",
                "Pharmacokinetics",
                "Pharmacodynamics",
                "Biomarkers",
                "Hidden",
            },
            sponsor_preferred_name="Flowchart Group",
            submission_value="FLWCRTGRP",
            extensible=True,
            approve=True,
        )

        self._activity_groups = {
            item.name: item for item in ActivityGroupService().get_all_concepts().items
        }

        self._activity_subgroups = {
            item.name: item
            for item in ActivitySubGroupService().get_all_concepts().items
        }

        self.activities = {
            item.name: item for item in ActivityService().get_all_concepts().items
        }

        for name, act in reversed(self.ACTIVITIES.items()):
            if name not in self.activities:
                self.create_activity(name, **act)

        for name, act in self.ACTIVITIES.items():
            self.create_study_activity(name, **act)

        self._activity_instance_classes = {
            item.name: item
            for item in ActivityInstanceClassService().get_all_items().items
        }

        for item in ActivityInstanceService().get_all_concepts().items:
            self.activity_instances.setdefault(item.activity_name, {})[item.name] = item

        self.create_activity_instances()

        self.get_study_activity_instances()
        self.assign_study_activity_instances()

        self._footnote_types = self.create_footnote_types()

        self.footnotes = self.create_footnotes(self.FOOTNOTES)

        self.soa_footnotes = self.create_soa_footnotes(self.FOOTNOTES)

        # Patch SoA Preferences as tests do not yet support baseline_as_time_zero
        self.soa_preferences = TestUtils.patch_soa_preferences(
            self.study.uid, baseline_as_time_zero=False
        )

    def create_codelist_with_terms(
        self, name: str, terms: Iterable[str], **kwargs
    ) -> dict[str, CTTerm]:
        term_names: set[str] = set(terms)
        ct_codelist_service = CTCodelistService()
        ct_term_service = CTTermService()

        # fetch or create codelist
        if codelists := ct_codelist_service.get_all_codelists(
            filter_by={"codelist_name_value.name": {"v": [name]}}
        ).items:
            # codelist exists
            self._codelists[name] = codelist = codelists[0]

        else:
            # create codelist
            self._codelists[name] = codelist = TestUtils.create_ct_codelist(
                name=name, **kwargs
            )
            log.info("created codelist: %s [%s]", codelist.name, codelist.codelist_uid)

        found_terms: list[CTTermNameAndAttributes]
        found_names: set[str]
        if term_names:
            # find terms in the codelist
            found_terms = ct_term_service.get_all_terms(
                codelist_name=None,
                codelist_uid=codelist.codelist_uid,
                library=None,
                package=None,
                filter_by={
                    "name.sponsor_preferred_name": {"v": list(term_names)},
                    "attributes.code_submission_value": {
                        "v": [t.upper() for t in term_names]
                    },
                },
                filter_operator=FilterOperator.OR,
            ).items

            # skip terms already in the codelist
            found_names = {
                n
                for item in found_terms
                for n in (
                    item.name.sponsor_preferred_name,
                    item.attributes.code_submission_value,
                )
            }
            term_names -= found_names

        if term_names:
            # find terms in any codelist
            found_terms = ct_term_service.get_all_terms(
                codelist_name=None,
                codelist_uid=None,
                library=None,
                package=None,
                filter_by={
                    "name.sponsor_preferred_name": {"v": list(term_names)},
                    "attributes.code_submission_value": {
                        "v": [t.upper() for t in term_names]
                    },
                },
                filter_operator=FilterOperator.OR,
            ).items

            # skip creation of already existing terms
            found_names = {
                n
                for item in found_terms
                for n in (
                    item.name.sponsor_preferred_name,
                    item.attributes.code_submission_value,
                )
            }
            term_names -= found_names

            # unique list of existing terms by term_uid, because duplicate items returned for each codelist it belongs to
            found_terms = {item.term_uid: item for item in found_terms}.values()

            # add existing terms to this codelist
            terms_added: list[CTTermNameAndAttributes] = []
            for item in found_terms:
                if item in terms_added:
                    continue

                ct_codelist_service.add_term(
                    codelist_uid=codelist.codelist_uid,
                    term_uid=item.term_uid,
                    order=1,
                )
                terms_added.append(item)

            if terms_added:
                log.info(
                    "added terms into codelist %s [%s]: %s",
                    codelist.name,
                    codelist.codelist_uid,
                    {
                        term.term_uid: term.name.sponsor_preferred_name
                        for term in terms_added
                    },
                )

        if term_names:
            # create missing terms into this codelist
            terms_created: list[CTTerm] = []

            for term_name in term_names:
                terms_created.append(
                    TestUtils.create_ct_term(
                        codelist_uid=codelist.codelist_uid,
                        code_submission_value=term_name.upper(),
                        sponsor_preferred_name=term_name,
                        library_name=codelist.library_name,
                    )
                )

            if terms_created:
                log.info(
                    "created terms into codelist %s [%s]: %s",
                    codelist.name,
                    codelist.codelist_uid,
                    {
                        term.term_uid: term.sponsor_preferred_name
                        for term in terms_created
                    },
                )

        return {
            item.name.sponsor_preferred_name: CTTerm.from_ct_term_name_and_attributes(
                item
            )
            for item in ct_term_service.get_all_terms(
                codelist_name=None,
                codelist_uid=codelist.codelist_uid,
                library=None,
                package=None,
                filter_by={
                    "name.sponsor_preferred_name": {"v": terms},
                    "attributes.code_submission_value": {
                        "v": [t.upper() for t in terms]
                    },
                },
                filter_operator=FilterOperator.OR,
            ).items
        }

    def create_epoch_terms(self) -> dict[str, CTTerm]:
        term_names = {"Screening", "Follow-Up", "Observation", "Run-in", "Treatment"}
        ct_term_service = CTTermService()

        terms = self.create_codelist_with_terms(
            name=settings.study_epoch_epoch_name,
            terms=term_names,
            sponsor_preferred_name=settings.study_epoch_epoch_name,
            submission_value="EPOCH",
            extensible=True,
            library_name="CDISC",
            approve=True,
        )

        for term in terms.values():
            try:
                ct_term_service.add_parent(
                    term.term_uid,
                    term.term_uid,
                    TermParentType.PARENT_TYPE.value,
                )
            except exceptions.AlreadyExistsException:
                pass
            try:
                ct_term_service.add_parent(
                    term.term_uid,
                    term.term_uid,
                    TermParentType.PARENT_SUB_TYPE.value,
                )
            except exceptions.AlreadyExistsException:
                pass

        self.create_codelist_with_terms(
            name=settings.study_epoch_type_name,
            terms=term_names,
            sponsor_preferred_name=settings.study_epoch_type_name,
            submission_value="EPOCHTP",
            extensible=True,
            library_name="Sponsor",
            approve=True,
        )

        self.create_codelist_with_terms(
            name=settings.study_epoch_subtype_name,
            terms=term_names,
            sponsor_preferred_name=settings.study_epoch_subtype_name,
            submission_value="EPOCHSTP",
            extensible=True,
            library_name="Sponsor",
            approve=True,
        )

        return terms

    def create_study_epochs(self, epoch_dict) -> dict[str, StudyEpoch]:
        log.debug("creating StudyEpochs")

        epochs = {}

        for k, epo in epoch_dict.items():
            epoch = TestUtils.create_study_epoch(
                study_uid=self.study.uid,
                epoch_subtype=self._epoch_terms[k].term_uid,
                color_hash=epo.get("color_hash"),
            )

            epochs[k] = epoch

        log.info(
            "created StudyEpochs: %s",
            {
                epoch.uid: epoch.epoch_subtype_ctterm.sponsor_preferred_name
                for epoch in epochs.values()
            },
        )

        return epochs

    def create_study_visits(self, visits_dict) -> dict[str, StudyVisit]:
        log.debug("creating StudyVisits")

        created_visits = {}
        visit_grouping: dict[Any, Any] = {}

        for k, vis in visits_dict.items():
            epoch = self.study_epochs[vis["epoch"]]
            visit_group = vis.get("visit_group", None)

            visit = TestUtils.create_study_visit(
                study_uid=self.study.uid,
                study_epoch_uid=epoch.uid,
                visit_type_uid=self._visit_type_terms[
                    vis.get("type", "Treatment")
                ].term_uid,
                time_reference_uid=self._visit_timeref_terms[
                    "Global anchor visit"
                ].term_uid,
                time_value=vis["day"],
                time_unit_uid=self._unit_definitions["day"].uid,
                visit_sublabel_reference=None,
                show_visit=True,
                min_visit_window_value=vis.get("min_window", 0),
                max_visit_window_value=vis.get("max_window", 0),
                visit_window_unit_uid=self._unit_definitions["days"].uid,
                description=None,
                start_rule=None,
                end_rule=None,
                visit_contact_mode_uid=self._visit_contact_terms[
                    vis["visit_contact_mode"]
                ].term_uid,
                epoch_allocation_uid=None,
                visit_class="SINGLE_VISIT",
                visit_subclass="SINGLE_VISIT",
                is_global_anchor_visit=vis.get("is_global_anchor_visit", False),
            )

            if visit_group:
                visit_grouping.setdefault(visit_group, []).append(visit)

            created_visits[k] = visit

        log.info(
            "StudyVisits: %s",
            {k: visit.uid for k, visit in created_visits.items()},
        )

        visit_service = StudyVisitService(study_uid=self.study.uid)
        for key, visits in visit_grouping.items():
            log.info(
                "Grouping StudyVisits: %s",
                [visit.uid for visit in visits],
            )

            visit_service.assign_visit_consecutive_group(
                study_uid=self.study.uid,
                visits_to_assign=[visit.uid for visit in visits],
                overwrite_visit_from_template=None,
                group_format=(
                    VisitGroupFormat.LIST if "," in key else VisitGroupFormat.RANGE
                ),
            )

        return created_visits

    def create_activity(self, name: str, **kwargs) -> Activity:
        # get activity group
        group_name = kwargs.get("group")
        if group_name and group_name not in self._activity_groups:
            self._activity_groups[group_name] = TestUtils.create_activity_group(
                name=group_name
            )

        # get activity subgroup
        subgroup_name = kwargs.get("subgroup")
        if subgroup_name and subgroup_name not in self._activity_subgroups:
            self._activity_subgroups[subgroup_name] = (
                TestUtils.create_activity_subgroup(
                    name=subgroup_name,
                    activity_groups=(
                        [self._activity_groups[group_name].uid] if group_name else []
                    ),
                )
            )

        # create activity
        self.activities[name] = activity = TestUtils.create_activity(
            name=name,
            activity_groups=(
                [self._activity_groups[group_name].uid] if group_name else []
            ),
            activity_subgroups=(
                [self._activity_subgroups[subgroup_name].uid] if subgroup_name else []
            ),
            library_name=kwargs.get("library_name", "Sponsor"),
        )

        log.info("created Activity[%s]: %s", activity.uid, activity.name)

        return activity

    def create_activity_instances(self) -> list[ActivityInstance]:
        log.debug("creating ActivityInstances")

        activity_instances_created = []

        for name, act in self.ACTIVITIES.items():
            activity = self.activities[name]
            existing_instances = self.activity_instances.get(name, {})

            for inst in act.get("instances", []):
                if inst["name"] in existing_instances:
                    continue

                if not (
                    instance_class := self._activity_instance_classes.get(inst["class"])
                ):
                    self._activity_instance_classes[inst["class"]] = (
                        instance_class := TestUtils.create_activity_instance_class(
                            name=inst["class"]
                        )
                    )

                activity_instance = TestUtils.create_activity_instance(
                    name=inst["name"],
                    activity_instance_class_uid=instance_class.uid,
                    name_sentence_case=inst["name"].lower(),
                    topic_code=inst.get("topic_code", None),
                    adam_param_code=inst.get("adam_param_code", None),
                    is_required_for_activity=True,
                    activities=[activity.uid],
                    activity_groups=(
                        [activity.activity_groupings[0].activity_group_uid]
                        if activity.activity_groupings
                        else []
                    ),
                    activity_subgroups=(
                        [activity.activity_groupings[0].activity_subgroup_uid]
                        if activity.activity_groupings
                        else []
                    ),
                    activity_items=[],
                )

                activity_instances_created.append(activity_instance)
                self.activity_instances.setdefault(name, {})[
                    inst["name"]
                ] = activity_instance

        log.info(
            "created ActivityInstances: %s",
            {
                activity_instance.uid: activity_instance.name
                for activity_instance in activity_instances_created
            },
        )

        return activity_instances_created

    def create_study_activity(self, name, **kwargs) -> StudySelectionActivity:
        """creates a StudySelectionActivity with StudyActivitySchedule, also creating Activity if needed"""

        # get or create Activity
        if not (activity := self.activities.get(name)):
            activity = self.create_activity(name, **kwargs)

        # create StudySelectionActivity
        self.study_activities[name] = study_activity = TestUtils.create_study_activity(
            study_uid=self.study.uid,
            activity_uid=activity.uid,
            activity_group_uid=(
                activity.activity_groupings[0].activity_group_uid
                if activity.activity_groupings
                else None
            ),
            activity_subgroup_uid=(
                activity.activity_groupings[0].activity_subgroup_uid
                if activity.activity_groupings
                else None
            ),
            soa_group_term_uid=(
                self._soa_group_terms[kwargs["soa_group"]].term_uid
                if kwargs.get("soa_group")
                else None
            ),
        )

        log.info(
            "created StudyActivity: %s [%s]",
            study_activity.activity.name,
            study_activity.study_activity_uid,
        )

        # set visibility in SoA
        TestUtils.patch_study_activity_schedule(
            study_uid=self.study.uid,
            study_selection_uid=study_activity.study_activity_uid,
            show_activity_in_protocol_flowchart=kwargs.get("show_activity"),
            show_activity_subgroup_in_protocol_flowchart=kwargs.get("show_subgroup"),
            show_activity_group_in_protocol_flowchart=kwargs.get("show_group"),
            show_soa_group_in_protocol_flowchart=kwargs.get("show_soa_group", False),
            soa_group_term_uid=(
                self._soa_group_terms[kwargs["soa_group"]].term_uid
                if kwargs.get("soa_group")
                else None
            ),
        )

        # create StudyActivitySchedules
        schedules = []
        for visit_name in kwargs.get("visits", []):
            try:
                study_visit = self.study_visits[visit_name]
            except KeyError as e:
                raise ValueError(
                    f"Study visit '{visit_name}' not found in {self.__class__.__name__} data"
                ) from e
            schedule = TestUtils.create_study_activity_schedule(
                study_uid=self.study.uid,
                study_activity_uid=study_activity.study_activity_uid,
                study_visit_uid=study_visit.uid,
            )
            schedules.append(schedule)
            self.study_activity_schedules.append(schedule)

        log.info(
            "created StudyActivitySchedules: %s",
            ", ".join(schedule.study_activity_schedule_uid for schedule in schedules),
        )

        return study_activity

    def get_study_activity_instances(
        self,
    ):
        log.debug("fetching StudyActivityInstances")

        study_activity_instances: list[StudySelectionActivityInstance] = (
            StudyActivityInstanceSelectionService()
            .get_all_selection(study_uid=self.study.uid)
            .items
        )

        log.info(
            "fetched StudyActivityInstances: %s",
            ", ".join(
                sai.study_activity_instance_uid for sai in study_activity_instances
            ),
        )

        self.study_activity_instances = {}
        for ssa in study_activity_instances:
            self.study_activity_instances.setdefault(ssa.study_activity_uid, []).append(
                ssa
            )

    def assign_study_activity_instances(self):
        for name in self.ACTIVITIES:
            if name not in self.activity_instances:
                continue

            study_activity_uid = self.study_activities[name].study_activity_uid

            TestUtils.batch_select_study_activity_instances(
                study_uid=self.study.uid,
                study_activity_uid=study_activity_uid,
                activity_instance_uids=[
                    activity_instance.uid
                    for activity_instance in self.activity_instances[name].values()
                ],
            )

        self.get_study_activity_instances()

    def create_footnote_types(
        self,
    ) -> dict[str, CTTerm]:
        terms: list[CTTerm] = []

        terms = self.create_codelist_with_terms(
            name="Footnote Type",
            terms=["SoA Footnote"],
            sponsor_preferred_name="Footnote Type",
            submission_value="FTNTTP",
            extensible=True,
            approve=True,
        )

        return terms

    def create_footnotes(self, footnotes_dict) -> dict[str, Footnote]:
        log.debug("creating footnotes")
        footnote_templates = {
            item.name_plain: item for item in FootnoteTemplateService().get_all().items
        }
        footnotes: dict[str, Footnote] = {
            item.name_plain: item for item in FootnoteService().get_all().items
        }
        footnotes_created = []

        for name in footnotes_dict:
            if name in footnotes:
                continue

            template: FootnoteTemplate
            if not (template := footnote_templates.get(name)):
                template = TestUtils.create_footnote_template(
                    name=f"<p>{name}</p>",
                    type_uid=self._footnote_types["SoA Footnote"].term_uid,
                    approve=True,
                )
            footnotes[name] = footnote = TestUtils.create_footnote(
                footnote_template_uid=template.uid,
                approve=True,
            )
            footnotes_created.append(footnote)

        if footnotes_created:
            log.info(
                "created Footnotes: %s",
                {fn.uid: {"template": fn.template.uid} for fn in footnotes_created},
            )

        return footnotes

    def create_soa_footnotes(self, footnotes_dict) -> list[StudySoAFootnote]:
        log.debug("creating StudySoAFootnotes")

        # Map activity group names to uid
        study_soa_group_uids = defaultdict(set)
        study_activity_group_uids = defaultdict(set)
        study_activity_subgroup_uids = defaultdict(set)

        for activity in self.study_activities.values():
            study_soa_group_uids[activity.study_soa_group.soa_group_term_name].add(
                activity.study_soa_group.study_soa_group_uid
            )

            if activity.study_activity_group:
                study_activity_group_uids[
                    activity.study_activity_group.activity_group_name
                ].add(activity.study_activity_group.study_activity_group_uid)

            if activity.study_activity_subgroup:
                study_activity_subgroup_uids[
                    activity.study_activity_subgroup.activity_subgroup_name
                ].add(activity.study_activity_subgroup.study_activity_subgroup_uid)

        # Map activity+visit uids to schedule uids
        study_activity_schedule_uids = {}
        for schedule in self.study_activity_schedules:
            study_activity_schedule_uids[
                schedule.study_activity_uid, schedule.study_visit_uid
            ] = schedule.study_activity_schedule_uid

        soa_footnotes: list[StudySoAFootnote] = []

        for name, refs in footnotes_dict.items():
            footnote: Footnote = self.footnotes[name]
            referenced_items = []

            for ref in refs:
                uids = set()
                typ = ref.get("type")
                assert typ
                assert typ in {t.value for t in SoAItemType}

                if typ == SoAItemType.STUDY_ACTIVITY_SCHEDULE.value:
                    visit_name = ref.get("visit")
                    activity_name = ref.get("activity")

                    assert visit_name and activity_name

                    assert visit_name in self.study_visits
                    visit_uid = self.study_visits[visit_name].uid

                    assert activity_name in self.study_activities
                    activity_uid = self.study_activities[
                        activity_name
                    ].study_activity_uid
                    name = activity_name

                    assert (
                        activity_uid,
                        visit_uid,
                    ) in study_activity_schedule_uids, (
                        f"{typ} '{name}' not scheduled for visit '{visit_name}'"
                    )
                    uids = {study_activity_schedule_uids[activity_uid, visit_uid]}
                    name = f"{name} {visit_name}"

                else:
                    assert (name := ref.get("name"))

                    if typ == SoAItemType.STUDY_EPOCH.value:
                        assert name in self.study_epochs
                        uids = {self.study_epochs[name].uid}

                    if typ == SoAItemType.STUDY_VISIT.value:
                        assert name in self.study_visits
                        uids = {self.study_visits[name].uid}

                    if typ == SoAItemType.STUDY_ACTIVITY.value:
                        assert name in self.study_activities
                        uids = {self.study_activities[name].study_activity_uid}

                    if typ == SoAItemType.STUDY_SOA_GROUP.value:
                        assert name in study_soa_group_uids
                        uids = study_soa_group_uids[name]

                    if typ == SoAItemType.STUDY_ACTIVITY_GROUP.value:
                        assert name in study_activity_group_uids
                        uids = study_activity_group_uids[name]

                    if typ == SoAItemType.STUDY_ACTIVITY_SUBGROUP.value:
                        assert name in study_activity_subgroup_uids
                        uids = study_activity_subgroup_uids[name]

                assert uids, f"Footnote reference type '{typ}' not implemented"

                for uid in uids:
                    referenced_items.append(
                        ReferencedItem(item_name=name, item_type=typ, item_uid=uid)
                    )

            soa_footnotes.append(
                TestUtils.create_study_soa_footnote(
                    study_uid=self.study.uid,
                    footnote_uid=footnote.uid,
                    referenced_items=referenced_items,
                )
            )

        log.info(
            "created StudySoAFootnotes: %s",
            {fn.uid: {"template": fn.template.uid} for fn in self.footnotes.values()},
        )

        return soa_footnotes


class SoATestDataMinimal(SoATestData):
    """A dirty subclass of SoATestData to create the minimum test data needed for a SoA

    Activities, instances, footnotes, groupings may not be shared with SoATestData,
    as its constructor does not check for existing data and may fail.
    """

    EPOCHS = {
        "Screening": {"color_hash": "#80DEEAFF"},
    }
    VISITS = {
        "V1": {
            "epoch": "Screening",
            "type": "Screening",
            "visit_contact_mode": "On Site Visit",
            "is_global_anchor_visit": True,
            "day": 0,
            "min_window": -7,
            "max_window": 3,
        },
    }
    NUM_VISIT_COLS = 1

    # Mind if an activity is scheduled for a visit of a visit-group, then it must be scheduled for all visits of the group.
    # Testing for safeguards on this is not in the scope of the tests of the SoA feature.
    ACTIVITIES = {
        "Acetaminophen": {
            "soa_group": "Pharmacodynamics",
            "group": "PK Sampling",
            "subgroup": "PK",
            "visits": ["V1"],
            "show_soa_group": True,
            "show_group": True,
            "show_subgroup": True,
            "show_activity": True,
            "instances": [
                {
                    "class": "Numeric finding",
                    "name": "Sample PK",
                    "topic_code": "PKPK",
                    "adam_param_code": "PKSPLE",
                }
            ],
        },
    }

    FOOTNOTES = {
        "Some footnote": [
            {
                "type": SoAItemType.STUDY_ACTIVITY_SCHEDULE.value,
                "visit": "V1",
                "activity": "Acetaminophen",
            },
        ]
    }


def test_soa_test_data_creation(temp_database_populated):
    """Ensures that SoATestData() create the expected test data by checking the dimensions of the SoA tables"""

    test_data = SoATestData(project=temp_database_populated.project)
    study_flowchart_service = StudyFlowchartService()

    soa_table: TableWithFootnotes = study_flowchart_service.build_flowchart_table(
        study_uid=test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.DETAILED,
    )
    assert (
        len(soa_table.rows) == test_data.NUM_SOA_ROWS + soa_table.num_header_rows
    ), "SoA table num rows mismatch"
    assert len(soa_table.footnotes) == len(
        test_data.footnotes
    ), "SoA table num footnotes mismatch"

    soa_table = study_flowchart_service.build_flowchart_table(
        study_uid=test_data.study.uid,
        study_value_version=None,
        layout=SoALayout.OPERATIONAL,
    )
    assert (
        len(soa_table.rows)
        == test_data.NUM_OPERATIONAL_SOA_ROWS + soa_table.num_header_rows
    ), "SoA table num rows mismatch"
    assert (
        len(soa_table.rows[-1].cells) == len(test_data.VISITS) + 3
    ), "SoA table num cols mismatch"


def test_soa_test_data_multiple(temp_database_populated):
    # ensures that multiple SoATestDatas can be crated in the same db
    SoATestDataMinimal(project=temp_database_populated.project)
    SoATestDataMinimal(project=temp_database_populated.project)
