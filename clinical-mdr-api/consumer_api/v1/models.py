import logging
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Self

from pydantic import BaseModel, Field

from common.utils import TimeUnit, VisitClass, VisitSubclass, convert_to_datetime

log = logging.getLogger(__name__)


class SortOrder(Enum):
    ASC = "asc"
    DESC = "desc"


class SortByStudies(Enum):
    UID = "uid"
    ID_PREFIX = "id_prefix"
    NUMBER = "number"


class Study(BaseModel):
    class StudyVersion(BaseModel):
        version_status: Annotated[
            str | None,
            Field(description="Study Status", json_schema_extra={"nullable": True}),
        ] = None
        version_number: Annotated[
            str | None,
            Field(
                description="Study Version Number", json_schema_extra={"nullable": True}
            ),
        ] = None
        version_started_at: Annotated[
            datetime,
            Field(
                description="Study Version Start Time",
            ),
        ]
        version_ended_at: Annotated[
            datetime | None,
            Field(
                description="Study Version End Time",
                json_schema_extra={"nullable": True},
            ),
        ] = None
        version_author: Annotated[
            str | None,
            Field(description="Study Author", json_schema_extra={"nullable": True}),
        ] = None
        version_description: Annotated[
            str | None,
            Field(
                description="Study Description", json_schema_extra={"nullable": True}
            ),
        ] = None

        @classmethod
        def from_input(cls, val: dict[str, Any]):
            log.debug("Create Study Version from input: %s", val)

            author_id = val.get("version_author_id", None)
            author_username = next(
                (
                    x["username"]
                    for x in val.get("all_authors", [])
                    if x.get("user_id") == author_id
                ),
                author_id,
            )

            return cls(
                version_status=val.get("version_status", None),
                version_number=val.get("version_number", None),
                version_started_at=convert_to_datetime(
                    val.get("version_started_at", None)
                ),
                version_ended_at=convert_to_datetime(val.get("version_ended_at", None)),
                version_author=author_username,
                version_description=val.get("version_description", None),
            )

    uid: Annotated[str, Field(description="Study UID")]
    id: Annotated[str, Field(description="Study ID")]
    id_prefix: Annotated[str, Field(description="Study ID prefix")]
    number: Annotated[
        str | None,
        Field(description="Study number", json_schema_extra={"nullable": True}),
    ] = None
    acronym: Annotated[
        str | None,
        Field(description="Study acronym", json_schema_extra={"nullable": True}),
    ] = None
    versions: Annotated[list[StudyVersion], Field(description="Study versions")]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study from input: %s", val)
        return cls(
            uid=val["uid"],
            id=val["id"],
            id_prefix=val["id_prefix"],
            number=val["number"],
            acronym=val.get("acronym", None),
            versions=[
                Study.StudyVersion.from_input(version)
                for version in val.get("versions", [])
            ],
        )


class SortByStudyVisits(Enum):
    UID = "uid"
    NAME = "visit_name"
    UNIQUE_VISIT_NUMBER = "unique_visit_number"


class StudyVisit(BaseModel):
    study_uid: Annotated[str, Field(description="Study UID")]
    uid: Annotated[str, Field(description="Study Visit UID")]

    visit_class: Annotated[VisitClass, Field(description="Study Visit Class name")]
    visit_subclass: Annotated[
        VisitSubclass | None,
        Field(
            description="Study Visit Sub Class name",
            json_schema_extra={"nullable": True},
        ),
    ] = None

    visit_name: Annotated[str, Field(description="Study Visit Name")]
    visit_order: Annotated[int, Field(description="Study Visit Order")]
    unique_visit_number: Annotated[
        int, Field(description="Study Visit Unique Visit Number")
    ]
    visit_number: Annotated[float, Field(description="Study Visit Visit Number")]
    visit_short_name: Annotated[str, Field(description="Study Visit Visit Short Name")]
    visit_window_min: Annotated[
        int | None,
        Field(
            description="Study Visit Min Visit Window Value",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_window_max: Annotated[
        int | None,
        Field(
            description="Study Visit Max Visit Window Value",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    is_global_anchor_visit: Annotated[
        bool | None,
        Field(
            description="Study Visit Global Anchor Visit",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_type_uid: Annotated[str, Field(description="Study Visit Visit Type UID")]
    visit_type_name: Annotated[str, Field(description="Study Visit Visit Type Name")]
    visit_window_unit_uid: Annotated[
        str | None,
        Field(
            description="Study Visit Visit Window Unit UID",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_window_unit_name: Annotated[
        str | None,
        Field(
            description="Study Visit Visit Window Unit Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    study_epoch_uid: Annotated[str, Field(description="Study Visit Study Epoch UID")]
    study_epoch_name: Annotated[str, Field(description="Study Visit Study Epoch Name")]
    time_unit_uid: Annotated[
        str | None,
        Field(
            description="Study Visit Time Unit UID",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time_unit_name: Annotated[
        str | None,
        Field(
            description="Study Visit Time Unit Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time_unit_object: Annotated[
        TimeUnit | None,
        Field(
            description="Study Visit Time Unit Name",
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    time_value_uid: Annotated[
        str | None,
        Field(
            description="Study Visit Time Value UID",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    time_value: Annotated[
        int | None,
        Field(
            description="Study Visit Time Value", json_schema_extra={"nullable": True}
        ),
    ] = None
    time_reference_name: Annotated[
        str | None,
        Field(
            description="Study Visit Time Reference Name",
            json_schema_extra={"nullable": True},
        ),
    ] = None
    visit_sublabel_reference: Annotated[
        str | None,
        Field(
            description="Anchor Visit UID for given StudyVisit",
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    anchor_visit: Annotated[
        Self,
        Field(
            description="Anchor Visit for given StudyVisit",
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    special_visit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None
    subvisit_number: Annotated[
        int | None,
        Field(
            json_schema_extra={"nullable": True},
            exclude=True,
        ),
    ] = None

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study Visit from input: %s", val)
        return cls(
            study_uid=val["study_uid"],
            uid=val["uid"],
            visit_class=VisitClass[val["visit_class"]],
            visit_subclass=(
                VisitSubclass[val["visit_subclass"]] if val["visit_subclass"] else None
            ),
            visit_name=val["visit_name"],
            unique_visit_number=val["unique_visit_number"],
            visit_number=val["visit_number"],
            visit_order=1,  # Default value, will be overridden later
            visit_short_name=str(val["visit_short_name"]),
            visit_window_min=val["visit_window_min"],
            visit_window_max=val["visit_window_max"],
            is_global_anchor_visit=val["is_global_anchor_visit"],
            visit_type_uid=val["visit_type_uid"],
            visit_type_name=val["visit_type_name"],
            visit_window_unit_uid=val["visit_window_unit_uid"],
            visit_window_unit_name=val["visit_window_unit_name"],
            study_epoch_uid=val["study_epoch_uid"],
            study_epoch_name=val["study_epoch_name"],
            time_unit_uid=val["time_unit_uid"],
            time_unit_name=val["time_unit_name"],
            time_unit_object=TimeUnit(
                name=val["time_unit_name"],
                conversion_factor_to_master=val[
                    "time_unit_conversion_factor_to_master"
                ],
            ),
            time_value_uid=val["time_value_uid"],
            time_value=val["time_value_value"],
            time_reference_name=val["time_reference_name"],
            visit_sublabel_reference=val["anchor_visit_uid"],
        )

    def get_absolute_duration(self) -> int | None:
        # Special visit doesn't have a timing but we want to place it
        # after the anchor visit for the special visit hence we derive timing based on the anchor visit
        if self.visit_class == VisitClass.SPECIAL_VISIT and self.anchor_visit:
            return self.anchor_visit.get_absolute_duration()
        if self.time_value is not None:
            if self.time_value == 0:
                return 0
            if self.anchor_visit is not None:
                return (
                    self.get_unified_duration()
                    + self.anchor_visit.get_absolute_duration()
                )
            return self.get_unified_duration()
        return None

    def get_unified_duration(self):
        return self.time_unit_object.from_timedelta(
            self.time_unit_object, self.time_value
        )


class SortByStudyActivities(Enum):
    UID = "uid"
    ACTIVITY_NAME = "activity_name"


class SortByStudyActivityInstances(Enum):
    UID = "uid"
    ACTIVITY_NAME = "activity.name"
    ACTIVITY_INSTANCE_NAME = "activity_instance.name"


class SortByLibraryItem(Enum):
    UID = "uid"
    NAME = "name"


class StudyActivity(BaseModel):
    study_uid: Annotated[str, Field(description="Study UID")]
    uid: Annotated[str, Field(description="Study Activity UID")]
    study_activity_subgroup: Annotated[
        dict | None,
        Field(
            description="Study Activity Subgroup", json_schema_extra={"nullable": True}
        ),
    ]
    study_activity_group: Annotated[
        dict | None,
        Field(description="Study Activity Group", json_schema_extra={"nullable": True}),
    ]
    soa_group: Annotated[dict, Field(description="SoA Group")]
    activity_uid: Annotated[str, Field(description="Activity UID")]
    activity_name: Annotated[str, Field(description="Activity Name")]
    activity_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    is_data_collected: Annotated[bool, Field(description="Activity Is Data Collected")]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study Visit from input: %s", val)
        return cls(
            study_uid=val["study_uid"],
            uid=val["uid"],
            study_activity_subgroup=val["study_activity_subgroup"],
            study_activity_group=val["study_activity_group"],
            soa_group=val["soa_group"],
            activity_uid=val["activity_uid"],
            activity_name=val["activity_name"],
            activity_nci_concept_id=val.get("nci_concept_id", None),
            activity_nci_concept_name=val.get("nci_concept_name", None),
            is_data_collected=val["is_data_collected"],
        )


class StudyActivityInstance(BaseModel):

    class Activity(BaseModel):
        uid: Annotated[str, Field(description="Activity UID")]
        name: Annotated[str, Field(description="Activity Name")]
        nci_concept_id: Annotated[
            str | None,
            Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
        ] = None
        nci_concept_name: Annotated[
            str | None,
            Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
        ] = None
        order: Annotated[
            int | None,
            Field(description="Activity Order", json_schema_extra={"nullable": True}),
        ]
        version: Annotated[str, Field(description="Activity Version")]

    class ActivityInstance(BaseModel):
        uid: Annotated[str, Field(description="Activity Instance UID")]
        name: Annotated[str, Field(description="Activity Instance Name")]
        nci_concept_id: Annotated[
            str | None,
            Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
        ] = None
        nci_concept_name: Annotated[
            str | None,
            Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
        ] = None
        param_code: Annotated[
            str | None,
            Field(description="Param Code", json_schema_extra={"nullable": True}),
        ] = None
        topic_code: Annotated[
            str | None,
            Field(description="Topic Code", json_schema_extra={"nullable": True}),
        ] = None
        version: Annotated[str, Field(description="Activity Instance Version")]

    class SoaGroup(BaseModel):
        uid: Annotated[str, Field(description="SoA Group UID")]
        name: Annotated[str, Field(description="SoA Group Name")]
        order: Annotated[
            int | None,
            Field(description="SoA Group Order", json_schema_extra={"nullable": True}),
        ]
        selection_uid: Annotated[str, Field(description="SoA Group Selection UID")]

    class StudyActivityGroup(BaseModel):
        uid: Annotated[str, Field(description="Study Activity Group UID")]
        name: Annotated[str, Field(description="Study Activity Group Name")]
        order: Annotated[
            int | None,
            Field(
                description="Study Activity Group Order",
                json_schema_extra={"nullable": True},
            ),
        ]
        selection_uid: Annotated[
            str, Field(description="Study Activity Group Selection UID")
        ]

    class StudyActivitySubgroup(BaseModel):
        uid: Annotated[str, Field(description="Study Activity Subgroup UID")]
        name: Annotated[str, Field(description="Study Activity Subgroup Name")]
        order: Annotated[
            int | None,
            Field(
                description="Study Activity Subgroup Order",
                json_schema_extra={"nullable": True},
            ),
        ]
        selection_uid: Annotated[
            str, Field(description="Study Activity Subgroup Selection UID")
        ]

    study_uid: Annotated[str, Field(description="Study UID")]
    uid: Annotated[str, Field(description="Study Activity Instance UID")]
    soa_group: Annotated[SoaGroup, Field(description="SoA Group")]
    study_activity_group: Annotated[
        StudyActivityGroup, Field(description="Study Activity Group")
    ]

    study_activity_subgroup: Annotated[
        StudyActivitySubgroup,
        Field(description="Study Activity Subgroup"),
    ]
    activity: Annotated[
        Activity,
        Field(description="Library Activity"),
    ]
    activity_instance: Annotated[
        ActivityInstance | None,
        Field(
            description="Library Activity Instance",
            json_schema_extra={"nullable": True},
        ),
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            study_uid=val["study_uid"],
            uid=val["uid"],
            study_activity_subgroup=val["study_activity_subgroup"],
            study_activity_group=val["study_activity_group"],
            soa_group=val["study_soa_group"],
            activity_instance=val["activity_instance"],
            activity=val["activity"],
        )


class SortByStudyDetailedSoA(Enum):
    VISIT_NAME = "visit_short_name"
    EPOCH_NAME = "epoch_name"
    ACTIVITY_NAME = "activity_name"
    ACTIVITY_GROUP_NAME = "activity_group_name"
    ACTIVITY_SUBGROUP_NAME = "activity_subgroup_name"
    SOA_GROUP_NAME = "soa_group_name"


class StudyDetailedSoA(BaseModel):
    study_uid: Annotated[str, Field(description="Study UID")]
    study_activity_uid: Annotated[str, Field(description="Study Activity UID")]
    visit_short_name: Annotated[str, Field(description="Study Visit Short Name")]
    epoch_name: Annotated[str, Field(description="Study Epoch Name")]
    activity_uid: Annotated[str, Field(description="Activity UID")]
    activity_name: Annotated[str, Field(description="Activity Name")]
    activity_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    activity_subgroup_name: Annotated[
        str | None,
        Field(
            description="Activity Subgroup Name", json_schema_extra={"nullable": True}
        ),
    ]
    activity_group_name: Annotated[
        str | None,
        Field(description="Activity Group Name", json_schema_extra={"nullable": True}),
    ]
    soa_group_name: Annotated[str, Field(description="SoA Group Name")]
    is_data_collected: Annotated[bool, Field(description="Activity Is Data Collected")]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            study_uid=val["study_uid"],
            study_activity_uid=val["study_activity_uid"],
            visit_short_name=str(val["visit_short_name"]),
            epoch_name=val["epoch_name"],
            activity_uid=val["activity_uid"],
            activity_name=val["activity_name"],
            activity_nci_concept_id=val.get("activity_nci_concept_id", None),
            activity_nci_concept_name=val.get("activity_nci_concept_name", None),
            activity_subgroup_name=val["activity_subgroup_name"],
            activity_group_name=val["activity_group_name"],
            soa_group_name=val["soa_group_name"],
            is_data_collected=val["is_data_collected"],
        )


class SortByStudyOperationalSoA(Enum):
    ACTIVITY_NAME = "activity_name"
    VISIT_UID = "visit_uid"
    VISIT_NAME = "visit_short_name"


class StudyOperationalSoA(BaseModel):
    study_uid: Annotated[
        str | None, Field(description="Study UID", json_schema_extra={"nullable": True})
    ]
    study_id: Annotated[
        str | None, Field(description="Study ID", json_schema_extra={"nullable": True})
    ]
    study_activity_uid: Annotated[str, Field(description="Study Activity UID")]
    activity_name: Annotated[
        str | None,
        Field(description="Activity Name", json_schema_extra={"nullable": True}),
    ]
    activity_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    activity_uid: Annotated[
        str | None,
        Field(description="Activity UID", json_schema_extra={"nullable": True}),
    ]
    activity_group_name: Annotated[
        str | None,
        Field(description="Activity Group Name", json_schema_extra={"nullable": True}),
    ]
    activity_group_uid: Annotated[
        str | None,
        Field(description="Activity Group UID", json_schema_extra={"nullable": True}),
    ]
    activity_subgroup_name: Annotated[
        str | None,
        Field(
            description="Activity Subgroup Name", json_schema_extra={"nullable": True}
        ),
    ]
    activity_subgroup_uid: Annotated[
        str | None,
        Field(
            description="Activity Subgroup UID", json_schema_extra={"nullable": True}
        ),
    ]
    activity_instance_name: Annotated[
        str | None,
        Field(
            description="Activity Instance Name", json_schema_extra={"nullable": True}
        ),
    ]
    activity_instance_nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    activity_instance_nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    activity_instance_uid: Annotated[
        str | None,
        Field(
            description="Activity Instance UID", json_schema_extra={"nullable": True}
        ),
    ]
    epoch_name: Annotated[
        str | None,
        Field(description="Epoch Name", json_schema_extra={"nullable": True}),
    ]
    param_code: Annotated[
        str | None,
        Field(description="Param Code", json_schema_extra={"nullable": True}),
    ]
    soa_group_name: Annotated[
        str | None,
        Field(description="SoA Group Name", json_schema_extra={"nullable": True}),
    ]
    topic_code: Annotated[
        str | None,
        Field(description="Topic Code", json_schema_extra={"nullable": True}),
    ]
    visit_short_name: Annotated[
        str | None,
        Field(description="Visit Short Name", json_schema_extra={"nullable": True}),
    ]
    visit_uid: Annotated[
        str | None, Field(description="Visit UID", json_schema_extra={"nullable": True})
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        log.debug("Create Study Operational SoA from input: %s", val)
        return cls(
            study_uid=val["study_uid"],
            study_id=val["study_id"],
            study_activity_uid=val["study_activity_uid"],
            activity_name=val["activity_name"],
            activity_nci_concept_id=val.get("activity_nci_concept_id", None),
            activity_nci_concept_name=val.get("activity_nci_concept_name", None),
            activity_uid=val["activity_uid"],
            activity_group_name=val["activity_group_name"],
            activity_group_uid=val["activity_group_uid"],
            activity_subgroup_name=val["activity_subgroup_name"],
            activity_subgroup_uid=val["activity_subgroup_uid"],
            activity_instance_name=val["activity_instance_name"],
            activity_instance_nci_concept_id=val.get(
                "activity_instance_nci_concept_id", None
            ),
            activity_instance_nci_concept_name=val.get(
                "activity_instance_nci_concept_name", None
            ),
            activity_instance_uid=val["activity_instance_uid"],
            epoch_name=val["epoch_name"],
            param_code=val["param_code"],
            soa_group_name=val["soa_group_name"],
            topic_code=val["topic_code"],
            visit_short_name=str(val["visit_short_name"]),
            visit_uid=val["visit_uid"],
        )


class Library(Enum):
    SPONSOR = "Sponsor"
    REQUESTED = "Requested"


class LibraryItemStatus(Enum):
    FINAL = "Final"
    DRAFT = "Draft"
    RETIRED = "Retired"


class LibraryActivityGrouping(BaseModel):
    activity_group_uid: Annotated[str, Field(description="Activity Group UID")]
    activity_group_name: Annotated[str, Field(description="Activity Group Name")]
    activity_subgroup_uid: Annotated[str, Field(description="Activity Subgroup UID")]
    activity_subgroup_name: Annotated[str, Field(description="Activity Subgroup Name")]


class LibraryActivityGroupingWithActivity(LibraryActivityGrouping):
    activity_uid: Annotated[str, Field(description="Activity UID")]
    activity_name: Annotated[str, Field(description="Activity Name")]


class LibraryActivity(BaseModel):
    uid: Annotated[str, Field(description="Activity UID")]
    library: Annotated[str, Field(description="Library Name")]
    name: Annotated[str, Field(description="Activity Name")]
    definition: Annotated[
        str | None,
        Field(description="Activity Definition", json_schema_extra={"nullable": True}),
    ]
    nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    is_data_collected: Annotated[
        bool, Field(description="Is Data Collected for Activity")
    ]
    status: Annotated[LibraryItemStatus, Field(description="Activity Status")]
    version: Annotated[str, Field(description="Activity Version")]
    groupings: Annotated[
        list[LibraryActivityGrouping], Field(description="Activity Groups/Subgroups")
    ] = []

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            uid=val["uid"],
            library=val["library"],
            name=val["name"],
            definition=val.get("definition", None),
            nci_concept_id=val.get("nci_concept_id", None),
            nci_concept_name=val.get("nci_concept_name", None),
            is_data_collected=val["is_data_collected"],
            status=LibraryItemStatus(val["status"]),
            version=val["version"],
            groupings=[
                LibraryActivityGrouping(
                    activity_group_uid=grouping["activity_group"]["uid"],
                    activity_group_name=grouping["activity_group"]["name"],
                    activity_subgroup_uid=grouping["activity_subgroup"]["uid"],
                    activity_subgroup_name=grouping["activity_subgroup"]["name"],
                )
                for grouping in val.get("groupings", [])
            ],
        )


class LibraryActivityInstance(BaseModel):
    uid: Annotated[str, Field(description="Activity UID")]
    library: Annotated[str, Field(description="Library Name")]
    name: Annotated[str, Field(description="Activity Name")]
    definition: Annotated[
        str | None,
        Field(description="Activity Definition", json_schema_extra={"nullable": True}),
    ]
    nci_concept_id: Annotated[
        str | None,
        Field(description="NCI Concept ID", json_schema_extra={"nullable": True}),
    ] = None
    nci_concept_name: Annotated[
        str | None,
        Field(description="NCI Concept Name", json_schema_extra={"nullable": True}),
    ] = None
    topic_code: Annotated[
        str | None,
        Field(description="Topic Code", json_schema_extra={"nullable": True}),
    ] = None
    param_code: Annotated[
        str | None,
        Field(description="ADaM Parameter Code", json_schema_extra={"nullable": True}),
    ] = None
    status: Annotated[LibraryItemStatus, Field(description="Activity Status")]
    version: Annotated[str, Field(description="Activity Version")]
    groupings: Annotated[
        list[LibraryActivityGroupingWithActivity],
        Field(description="Activity Groups/Subgroups"),
    ] = []

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            uid=val["uid"],
            library=val["library_name"],
            name=val["name"],
            definition=val.get("definition", None),
            nci_concept_id=val.get("nci_concept_id", None),
            nci_concept_name=val.get("nci_concept_name", None),
            topic_code=val.get("topic_code", None),
            param_code=val.get("param_code", None),
            status=LibraryItemStatus(val["status"]),
            version=val["version"],
            groupings=[
                LibraryActivityGroupingWithActivity(
                    activity_uid=grouping["activity"]["uid"],
                    activity_name=grouping["activity"]["name"],
                    activity_group_uid=grouping["activity_group"]["uid"],
                    activity_group_name=grouping["activity_group"]["name"],
                    activity_subgroup_uid=grouping["activity_subgroup"]["uid"],
                    activity_subgroup_name=grouping["activity_subgroup"]["name"],
                )
                for grouping in val.get("activity_groupings", [])
            ],
        )


class PapillonsStudyMetaDataBase(BaseModel):
    project: Annotated[str, Field(description="Project")]
    study_number: Annotated[str, Field(description="Study Number")]
    subpart: Annotated[
        str | None,
        Field(description="Study Subpart", json_schema_extra={"nullable": True}),
    ]
    study: Annotated[
        str, Field(description="Full Study ID concatenate as: project-study")
    ]
    api_version: Annotated[str, Field(description="API Version")]
    study_version: Annotated[str, Field(description="Study Version")]
    specified_dt: Annotated[
        str | None,
        Field(
            description="Specified datetime which the released version before that datetime is returned.",
            json_schema_extra={"nullable": True},
        ),
    ]
    fetch_dt: Annotated[str, Field(description="Datetime when the data is fetched.")]


class PapillonsSoAItem(BaseModel):
    topic_cd: Annotated[str, Field(description="Topic code")]
    visits: Annotated[
        list[str], Field(description="Lists of visits which the activity was assessed.")
    ]

    # TODO: The below should be added when the data points are implemented
    # baseline_visits: Annotated[list[str], Field(description="Lists of visits which is considered baseline for the activity.")]
    # Important: Annotated[bool, Field(description="Indication for if the activity is considered important.")]
    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            topic_cd=val["topic_cd"],
            visits=val["visits"],
        )


class PapillonsSoA(PapillonsStudyMetaDataBase):
    SoA: Annotated[
        list[PapillonsSoAItem] | None, Field(description="Scheduled activities")
    ]

    @classmethod
    def from_input(cls, val: dict[str, Any]):
        return cls(
            project=val["project"],
            study_number=val["study_number"],
            subpart=val["subpart"],
            study=val["full_study_id"],
            api_version=val["api_version"],
            study_version=val["study_version"],
            specified_dt=val["specified_dt"],
            fetch_dt=val["fetch_dt"],
            SoA=[PapillonsSoAItem.from_input(n) for n in val["SoA"]],
        )
