from datetime import datetime
from typing import Annotated, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.domains.study_selections.study_epoch import StudyEpochEpoch
from clinical_mdr_api.domains.study_selections.study_visit import (
    StudyVisitContactMode,
    StudyVisitEpochAllocation,
    StudyVisitRepeatingFrequency,
    StudyVisitTimeReference,
    StudyVisitType,
    StudyVisitVO,
    VisitGroupFormat,
)
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameWithConflictFlag,
)
from clinical_mdr_api.models.utils import (
    BaseModel,
    PatchInputModel,
    PostInputModel,
    get_latest_on_datetime_str,
)
from common.config import settings


class StudyVisitCreateInput(PostInputModel):
    study_epoch_uid: Annotated[str, Field()]
    visit_type_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_visit_type.uid"})
    ]
    time_reference_uid: Annotated[str | None, Field()] = None
    time_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    time_unit_uid: Annotated[str | None, Field()] = None
    visit_sublabel_reference: Annotated[str | None, Field()] = None
    show_visit: Annotated[bool, Field()]
    min_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = -9999
    max_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = 9999
    visit_window_unit_uid: Annotated[str | None, Field()] = None
    description: Annotated[str | None, Field()] = None
    start_rule: Annotated[str | None, Field()] = None
    end_rule: Annotated[str | None, Field()] = None
    visit_contact_mode_uid: Annotated[str, Field()]
    epoch_allocation_uid: Annotated[str | None, Field()] = None
    visit_class: Annotated[str, Field()]
    visit_subclass: Annotated[str | None, Field()] = None
    is_global_anchor_visit: Annotated[bool, Field()]
    is_soa_milestone: Annotated[bool, Field()] = False
    visit_name: Annotated[str | None, Field()] = None
    visit_short_name: Annotated[str | None, Field()] = None
    visit_number: Annotated[float | None, Field()] = None
    unique_visit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    repeating_frequency_uid: Annotated[
        str | None, Field(json_schema_extra={"source": "has_repeating_frequency.uid"})
    ] = None


class StudyVisitEditInput(PatchInputModel):
    uid: Annotated[str, Field(description="Uid of the Visit")]
    study_epoch_uid: Annotated[str, Field()]
    visit_type_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_visit_type.uid"})
    ]
    time_reference_uid: Annotated[str | None, Field()] = None
    time_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ]
    time_unit_uid: Annotated[str | None, Field()] = None
    visit_sublabel_reference: Annotated[str | None, Field()] = None
    show_visit: Annotated[bool, Field()]
    min_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = -9999
    max_visit_window_value: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = 9999
    visit_window_unit_uid: Annotated[str | None, Field()] = None
    description: Annotated[str | None, Field()] = None
    start_rule: Annotated[str | None, Field()] = None
    end_rule: Annotated[str | None, Field()] = None
    visit_contact_mode_uid: Annotated[str, Field()]
    epoch_allocation_uid: Annotated[str | None, Field()] = None
    visit_class: Annotated[str, Field()]
    visit_subclass: Annotated[str | None, Field()] = None
    is_global_anchor_visit: Annotated[bool, Field()]
    is_soa_milestone: Annotated[bool, Field()] = False
    visit_name: Annotated[str | None, Field()] = None
    visit_short_name: Annotated[str | None, Field()] = None
    visit_number: Annotated[float | None, Field()] = None
    unique_visit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            gt=-settings.max_int_neo4j,
            lt=settings.max_int_neo4j,
        ),
    ] = None
    repeating_frequency_uid: Annotated[
        str | None, Field(json_schema_extra={"source": "has_repeating_frequency.uid"})
    ] = None


class SimpleStudyVisit(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str, Field(description="Uid of the visit", json_schema_extra={"source": "uid"})
    ]
    visit_name: Annotated[
        str,
        Field(
            description="Name of the visit",
            json_schema_extra={"source": "has_visit_name.has_latest_value.name"},
        ),
    ]
    visit_type_name: Annotated[
        str,
        Field(
            description="Name of the visit type",
            json_schema_extra={
                "source": "has_visit_type.has_name_root.has_latest_value.name"
            },
        ),
    ]


class StudyVisitBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)

    uid: Annotated[str, Field(description="Uid of the Visit")]
    study_epoch_uid: Annotated[str, Field()]
    visit_type_uid: Annotated[
        str, Field(json_schema_extra={"source": "has_visit_type.uid"})
    ]
    visit_sublabel_reference: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    consecutive_visit_group: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    show_visit: Annotated[bool, Field()]
    min_visit_window_value: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = -9999
    max_visit_window_value: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = 9999
    visit_window_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    description: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    start_rule: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    end_rule: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    study_uid: Annotated[str, Field()]
    study_id: Annotated[
        str | None,
        Field(
            description="The study ID like 'CDISC DEV-0'",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_version: Annotated[
        str | None,
        Field(
            description="Study version number, if specified, otherwise None.",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_epoch: Annotated[SimpleCTTermNameWithConflictFlag, Field()]
    # study_epoch_name can be calculated from uid
    epoch_uid: Annotated[str, Field(description="The uid of the study epoch")]

    visit_type: Annotated[SimpleCTTermNameWithConflictFlag, Field()]
    visit_type_name: Annotated[str, Field()]

    time_reference_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_reference_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_reference: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    time_value: Annotated[int | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    time_unit_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    time_unit: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    visit_contact_mode_uid: Annotated[str, Field()]
    visit_contact_mode: Annotated[SimpleCTTermNameWithConflictFlag, Field()]
    epoch_allocation_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    epoch_allocation: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    repeating_frequency_uid: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    repeating_frequency: Annotated[
        SimpleCTTermNameWithConflictFlag | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None

    duration_time: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    duration_time_unit: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    study_day_number: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_days: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_days_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_day_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_week_number: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_weeks: Annotated[
        int | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_duration_weeks_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    study_week_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    week_in_study_label: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    visit_number: Annotated[float, Field()]
    visit_subnumber: Annotated[int, Field()]

    unique_visit_number: Annotated[int, Field()]
    visit_subname: Annotated[str, Field()]

    visit_name: Annotated[str, Field()]
    visit_short_name: Annotated[str, Field()]

    visit_window_unit_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    visit_class: Annotated[str, Field()]
    visit_subclass: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_global_anchor_visit: Annotated[bool, Field()]
    is_soa_milestone: Annotated[bool, Field()]
    status: Annotated[str, Field(description="Study Visit status")]
    start_date: Annotated[datetime, Field(description="Study Visit creation date")]
    end_date: Annotated[
        datetime | None,
        Field(
            description="Study Visit last date of version",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    author_username: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(description="List of actions to perform on item"),
    ]
    change_type: Annotated[
        str | None,
        Field(description="Type of Action", json_schema_extra={"nullable": True}),
    ] = None

    @classmethod
    def transform_to_response_model(
        cls,
        visit: StudyVisitVO,
        study_value_version: str | None = None,
        derive_props_based_on_timeline: bool = True,
        use_global_mappings: bool = True,
    ) -> Self:
        timepoint = visit.timepoint
        if use_global_mappings:
            if timepoint:
                visit_timereference = StudyVisitTimeReference.get(
                    timepoint.visit_timereference.term_uid
                )
                timepoint.visit_timereference = visit_timereference
            visit.epoch_connector.epoch = StudyEpochEpoch.get(
                visit.epoch.epoch.term_uid
            )
            visit.visit_type = StudyVisitType.get(visit.visit_type.term_uid)
            visit.visit_contact_mode = StudyVisitContactMode.get(
                visit.visit_contact_mode.term_uid
            )
            epoch_allocation_uid = getattr(visit.epoch_allocation, "term_uid", None)
            if epoch_allocation_uid:
                visit.epoch_allocation = StudyVisitEpochAllocation.get(
                    epoch_allocation_uid
                )
            repeating_frequency_uid = getattr(
                visit.repeating_frequency, "term_uid", None
            )
            if repeating_frequency_uid:
                visit.repeating_frequency = StudyVisitRepeatingFrequency.get(
                    repeating_frequency_uid
                )
        return cls(
            visit_type_name=visit.visit_type.sponsor_preferred_name,
            uid=visit.uid,
            study_uid=visit.study_uid,
            study_id=(
                f"{visit.study_id_prefix}-{visit.study_number}"
                if visit.study_id_prefix and visit.study_number
                else None
            ),
            study_version=study_value_version or get_latest_on_datetime_str(),
            study_epoch_uid=visit.epoch_uid,
            study_epoch=visit.epoch.epoch,
            epoch_uid=visit.epoch.epoch.term_uid,
            order=visit.visit_order,
            visit_type_uid=visit.visit_type.term_uid,
            visit_type=visit.visit_type,
            time_reference_uid=(
                timepoint.visit_timereference.term_uid if timepoint else None
            ),
            time_reference_name=(
                timepoint.visit_timereference.sponsor_preferred_name
                if timepoint
                else None
            ),
            time_reference=getattr(timepoint, "visit_timereference", None),
            time_value=getattr(timepoint, "visit_value", None),
            time_unit_uid=getattr(timepoint, "time_unit_uid", None),
            time_unit_name=getattr(visit.time_unit_object, "name", None),
            duration_time=visit.get_absolute_duration() if timepoint else None,
            duration_time_unit=getattr(timepoint, "time_unit_uid", None),
            study_day_number=getattr(visit, "study_day_number", None),
            study_day_label=getattr(visit, "study_day_label", None),
            study_duration_days=getattr(visit.study_duration_days, "value", None),
            study_duration_days_label=getattr(visit, "study_duration_days_label", None),
            study_week_number=getattr(visit, "study_week_number", None),
            study_week_label=getattr(visit, "study_week_label", None),
            study_duration_weeks=getattr(visit.study_duration_weeks, "value", None),
            study_duration_weeks_label=getattr(
                visit, "study_duration_weeks_label", None
            ),
            week_in_study_label=getattr(visit, "week_in_study_label", None),
            visit_number=visit.visit_number,
            visit_subnumber=visit.visit_subnumber,
            unique_visit_number=(
                visit.unique_visit_number
                if derive_props_based_on_timeline
                else visit.vis_unique_number
            ),
            visit_subname=visit.visit_subname,
            visit_sublabel_reference=visit.visit_sublabel_reference,
            visit_name=visit.visit_name,
            visit_short_name=(
                str(visit.visit_short_name)
                if derive_props_based_on_timeline
                else visit.vis_short_name
            ),
            consecutive_visit_group=(
                visit.study_visit_group.group_name if visit.study_visit_group else None
            ),
            show_visit=visit.show_visit,
            min_visit_window_value=visit.visit_window_min,
            max_visit_window_value=visit.visit_window_max,
            visit_window_unit_uid=visit.window_unit_uid,
            visit_window_unit_name=(
                visit.window_unit_object.name if visit.window_unit_object else None
            ),
            description=visit.description,
            start_rule=visit.start_rule,
            end_rule=visit.end_rule,
            visit_contact_mode_uid=visit.visit_contact_mode.term_uid,
            visit_contact_mode=visit.visit_contact_mode,
            epoch_allocation_uid=(
                visit.epoch_allocation.term_uid if visit.epoch_allocation else None
            ),
            epoch_allocation=visit.epoch_allocation,
            status=visit.status.value,
            start_date=visit.start_date.strftime(settings.date_time_format),
            author_username=visit.author_username or visit.author_id,
            possible_actions=visit.possible_actions,
            visit_class=visit.visit_class.name,
            visit_subclass=visit.visit_subclass.name if visit.visit_subclass else None,
            is_global_anchor_visit=visit.is_global_anchor_visit,
            is_soa_milestone=visit.is_soa_milestone,
            repeating_frequency_uid=(
                visit.repeating_frequency.term_uid
                if visit.repeating_frequency
                else None
            ),
            repeating_frequency=visit.repeating_frequency,
        )


class StudyVisit(StudyVisitBase):
    order: Annotated[int, Field()]


class StudyVisitVersion(StudyVisitBase):
    changes: Annotated[list[str], Field()]


class AllowedTimeReferences(BaseModel):
    time_reference_uid: Annotated[str, Field()]
    time_reference_name: Annotated[str, Field()]


class VisitConsecutiveGroupInput(PostInputModel):
    visits_to_assign: Annotated[
        list[str],
        Field(
            description="List of visits to be assigned to the consecutive_visit_group",
            min_length=2,
        ),
    ]
    format: Annotated[
        VisitGroupFormat,
        Field(
            description="""The way how the Visits should be groupped. The possible values are: range or list.
                           The range technique will name the group in the following way (V4-V6),
                           the list technique will generate the group name in the following way (V4,V5,V6)""",
        ),
    ] = VisitGroupFormat.RANGE
    overwrite_visit_from_template: Annotated[
        str | None,
        Field(
            description="The uid of the visit from which get properties to overwrite"
        ),
    ] = None
