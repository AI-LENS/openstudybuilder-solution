from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.biomedical_concepts.activity_item_class import (
    ActivityItemClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import (
    BaseModel,
    InputModel,
    PatchInputModel,
    PostInputModel,
)
from common.config import settings


class CompactActivityInstanceClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None


class SimpleDataTypeTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str, Field(json_schema_extra={"source": "has_latest_value.has_data_type.uid"})
    ]
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_data_type.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class SimpleRoleTerm(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str, Field(json_schema_extra={"source": "has_latest_value.has_role.uid"})
    ]
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.has_role.has_name_root.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class SimpleVariableClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={"source": "maps_variable_class.uid", "nullable": True}
        ),
    ] = None


class ActivityItemClass(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_latest_value.name", "nullable": True}),
    ] = None
    definition: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.definition",
                "nullable": True,
            }
        ),
    ] = None
    order: Annotated[int, Field(json_schema_extra={"source": "has_latest_value.order"})]
    data_type: Annotated[SimpleDataTypeTerm, Field()]
    role: Annotated[SimpleRoleTerm, Field()]
    activity_instance_classes: Annotated[
        list[CompactActivityInstanceClass] | None, Field()
    ]
    variable_classes: Annotated[
        list[SimpleVariableClass] | None, Field(json_schema_extra={"nullable": True})
    ] = None
    library_name: Annotated[
        str, Field(json_schema_extra={"source": "has_library.name"})
    ]
    nci_concept_id: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.nci_concept_id",
                "nullable": True,
            }
        ),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            validate_default=True,
            description=(
                "Holds those actions that can be performed on the ActivityItemClasses. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]

    @field_validator("possible_actions", mode="before")
    @classmethod
    def validate_possible_actions(cls, _, info: ValidationInfo):
        if info.data["status"] == LibraryItemStatus.DRAFT.value and info.data[
            "version"
        ].startswith("0"):
            return [
                ObjectAction.APPROVE.value,
                ObjectAction.DELETE.value,
                ObjectAction.EDIT.value,
            ]
        if info.data["status"] == LibraryItemStatus.DRAFT.value:
            return [ObjectAction.APPROVE.value, ObjectAction.EDIT.value]
        if info.data["status"] == LibraryItemStatus.FINAL.value:
            return [
                ObjectAction.INACTIVATE.value,
                ObjectAction.NEWVERSION.value,
            ]
        if info.data["status"] == LibraryItemStatus.RETIRED.value:
            return [ObjectAction.REACTIVATE.value]
        return []

    @classmethod
    def from_activity_item_class_ar(
        cls,
        activity_item_class_ar: ActivityItemClassAR,
        find_activity_instance_class_by_uid: Callable[
            [str], ActivityInstanceClassAR | None
        ],
    ) -> Self:
        _activity_instance_classes = [
            find_activity_instance_class_by_uid(activity_instance_class.uid)
            for activity_instance_class in activity_item_class_ar.activity_item_class_vo.activity_instance_classes
        ]

        activity_instance_classes = []
        for activity_instance_class in _activity_instance_classes:
            rel = next(
                item
                for item in activity_instance_class.activity_instance_class_vo.activity_item_classes
                if item.uid == activity_item_class_ar.uid
            )
            activity_instance_classes.append(
                CompactActivityInstanceClass(
                    uid=activity_instance_class.uid,
                    name=activity_instance_class.name,
                    mandatory=rel.mandatory,
                    is_adam_param_specific_enabled=rel.is_adam_param_specific_enabled,
                )
            )

        return cls(
            uid=activity_item_class_ar.uid,
            name=activity_item_class_ar.name,
            definition=activity_item_class_ar.definition,
            nci_concept_id=activity_item_class_ar.nci_concept_id,
            order=activity_item_class_ar.activity_item_class_vo.order,
            activity_instance_classes=activity_instance_classes,
            data_type=SimpleDataTypeTerm(
                uid=activity_item_class_ar.activity_item_class_vo.data_type_uid,
                name=activity_item_class_ar.activity_item_class_vo.data_type_name,
            ),
            role=SimpleRoleTerm(
                uid=activity_item_class_ar.activity_item_class_vo.role_uid,
                name=activity_item_class_ar.activity_item_class_vo.role_name,
            ),
            variable_classes=(
                [
                    SimpleVariableClass(uid=variable_class_uid)
                    for variable_class_uid in activity_item_class_ar.activity_item_class_vo.variable_class_uids
                ]
                if activity_item_class_ar.activity_item_class_vo.variable_class_uids
                else []
            ),
            library_name=Library.from_library_vo(activity_item_class_ar.library).name,
            start_date=activity_item_class_ar.item_metadata.start_date,
            end_date=activity_item_class_ar.item_metadata.end_date,
            status=activity_item_class_ar.item_metadata.status.value,
            version=activity_item_class_ar.item_metadata.version,
            change_description=activity_item_class_ar.item_metadata.change_description,
            author_username=activity_item_class_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_item_class_ar.get_possible_actions()]
            ),
        )


class CompactActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"nullable": True}),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_instance_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None


class ActivityInstanceClassRelInput(InputModel):
    uid: Annotated[str, Field(min_length=1)]
    is_adam_param_specific_enabled: Annotated[bool, Field()]
    mandatory: Annotated[bool, Field()]


class ActivityItemClassCreateInput(PostInputModel):
    name: Annotated[str, Field()]
    definition: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int, Field(gt=0, lt=settings.max_int_neo4j)]
    activity_instance_classes: Annotated[list[ActivityInstanceClassRelInput], Field()]
    role_uid: Annotated[str, Field()]
    data_type_uid: Annotated[str, Field()]
    library_name: Annotated[str, Field()]


class ActivityItemClassEditInput(PatchInputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int | None, Field(gt=0, lt=settings.max_int_neo4j)] = None
    activity_instance_classes: list[ActivityInstanceClassRelInput] = Field(
        default_factory=list
    )
    library_name: Annotated[str | None, Field(min_length=1)] = None
    change_description: Annotated[str, Field(min_length=1)]
    role_uid: Annotated[str | None, Field(min_length=1)] = None
    data_type_uid: Annotated[str | None, Field(min_length=1)] = None


class ActivityItemClassMappingInput(PatchInputModel):
    variable_class_uids: list[str] = Field(default_factory=list)


class ActivityItemClassVersion(ActivityItemClass):
    """
    Class for storing ActivityItemClass and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)
