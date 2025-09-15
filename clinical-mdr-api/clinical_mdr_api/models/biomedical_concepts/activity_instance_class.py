from typing import Annotated, Callable, Self

from pydantic import ConfigDict, Field, ValidationInfo, field_validator

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.biomedical_concepts.activity_instance_class import (
    ActivityInstanceClassAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemStatus,
    ObjectAction,
)
from clinical_mdr_api.models.concepts.concept import VersionProperties
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel, InputModel, PatchInputModel


class ParentActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_activity_item_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None


class CompactActivityItemClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.uid",
                "nullable": True,
            }
        ),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class.has_latest_value.name",
                "nullable": True,
            }
        ),
    ] = None
    mandatory: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class|mandatory",
                "nullable": True,
            }
        ),
    ] = None
    is_adam_param_specific_enabled: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_activity_item_class|is_adam_param_specific_enabled",
                "nullable": True,
            }
        ),
    ] = None


class CompactActivityInstanceClass(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None,
        Field(json_schema_extra={"source": "parent_class.uid", "nullable": True}),
    ] = None
    name: Annotated[
        str | None,
        Field(
            json_schema_extra={
                "source": "parent_class.has_latest_value.name",
                "nullable": True,
            },
        ),
    ] = None


class ActivityInstanceClass(VersionProperties):
    model_config = ConfigDict(from_attributes=True)

    uid: Annotated[
        str | None, Field(json_schema_extra={"source": "uid", "nullable": True})
    ] = None
    name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_latest_value.name", "nullable": True}),
    ] = None
    order: Annotated[
        int | None,
        Field(json_schema_extra={"source": "has_latest_value.order", "nullable": True}),
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
    is_domain_specific: Annotated[
        bool | None,
        Field(
            json_schema_extra={
                "source": "has_latest_value.is_domain_specific",
                "nullable": True,
            },
        ),
    ] = None
    level: Annotated[
        int | None,
        Field(json_schema_extra={"source": "has_latest_value.level", "nullable": True}),
    ] = None
    parent_class: Annotated[
        CompactActivityInstanceClass | None, Field(json_schema_extra={"nullable": True})
    ] = None
    library_name: Annotated[
        str | None,
        Field(json_schema_extra={"source": "has_library.name", "nullable": True}),
    ] = None
    possible_actions: Annotated[
        list[str],
        Field(
            validate_default=True,
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
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
    def from_activity_instance_class_ar(
        cls,
        activity_instance_class_ar: ActivityInstanceClassAR,
        get_parent_class: Callable[[str], tuple[str, str] | None],
    ) -> Self:
        parent_class = get_parent_class(activity_instance_class_ar.uid)

        return cls(
            uid=activity_instance_class_ar.uid,
            name=activity_instance_class_ar.name,
            order=activity_instance_class_ar.activity_instance_class_vo.order,
            definition=activity_instance_class_ar.activity_instance_class_vo.definition,
            is_domain_specific=activity_instance_class_ar.activity_instance_class_vo.is_domain_specific,
            level=activity_instance_class_ar.activity_instance_class_vo.level,
            parent_class=(
                CompactActivityInstanceClass(
                    uid=parent_class[0],
                    name=parent_class[1],
                )
                if parent_class
                else None
            ),
            library_name=Library.from_library_vo(
                activity_instance_class_ar.library
            ).name,
            start_date=activity_instance_class_ar.item_metadata.start_date,
            end_date=activity_instance_class_ar.item_metadata.end_date,
            status=activity_instance_class_ar.item_metadata.status.value,
            version=activity_instance_class_ar.item_metadata.version,
            change_description=activity_instance_class_ar.item_metadata.change_description,
            author_username=activity_instance_class_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_instance_class_ar.get_possible_actions()]
            ),
        )


class ActivityInstanceClassInput(InputModel):
    name: Annotated[str | None, Field(min_length=1)] = None
    order: Annotated[int | None, Field()] = None
    definition: Annotated[str | None, Field(min_length=1)] = None
    is_domain_specific: Annotated[bool, Field()] = False
    level: Annotated[int | None, Field()] = None
    library_name: Annotated[str | None, Field(min_length=1)] = None
    parent_uid: Annotated[str | None, Field(min_length=1)] = None
    dataset_class_uid: Annotated[str | None, Field(min_length=1)] = None


class ActivityInstanceClassEditInput(ActivityInstanceClassInput):
    change_description: Annotated[str, Field(min_length=1)]


class ActivityInstanceClassMappingInput(PatchInputModel):
    dataset_class_uid: str


class ActivityInstanceClassVersion(ActivityInstanceClass):
    """
    Class for storing ActivityInstanceClass and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class ActivityInstanceClassWithDataset(BaseModel):
    uid: Annotated[str, Field(json_schema_extra={"nullable": False})]
    name: Annotated[
        str,
        Field(json_schema_extra={"nullable": False}),
    ]

    datasets: list[str] = Field(default_factory=list)
