from datetime import datetime
from typing import Annotated, Any, Callable, Self

from pydantic import ConfigDict, Field

from clinical_mdr_api.descriptions.general import CHANGES_FIELD_DESC
from clinical_mdr_api.domains.concepts.activities.activity import ActivityAR
from clinical_mdr_api.domains.concepts.activities.activity_group import ActivityGroupAR
from clinical_mdr_api.domains.concepts.activities.activity_instance import (
    ActivityInstanceAR,
)
from clinical_mdr_api.domains.concepts.activities.activity_item import LibraryItem
from clinical_mdr_api.domains.concepts.activities.activity_sub_group import (
    ActivitySubGroupAR,
)
from clinical_mdr_api.models.biomedical_concepts.activity_instance_class import (
    CompactActivityInstanceClass,
)
from clinical_mdr_api.models.concepts.activities.activity import (
    ActivityBase,
    ActivityGrouping,
    ActivityHierarchySimpleModel,
    SimpleActivityGroup,
    SimpleActivityGrouping,
    SimpleActivityInstance,
    SimpleActivityInstanceClass,
    SimpleActivitySubGroup,
)
from clinical_mdr_api.models.concepts.activities.activity_item import (
    ActivityItem,
    ActivityItemCreateInput,
    CompactActivityItemClass,
    CompactCTTerm,
    CompactOdmForm,
    CompactOdmItem,
    CompactOdmItemGroup,
    CompactUnitDefinition,
)
from clinical_mdr_api.models.concepts.concept import (
    ExtendedConceptPatchInput,
    ExtendedConceptPostInput,
)
from clinical_mdr_api.models.libraries.library import Library
from clinical_mdr_api.models.utils import BaseModel
from common.utils import convert_to_datetime


class ActivityInstanceHierarchySimpleModel(BaseModel):
    activity: Annotated[ActivityHierarchySimpleModel, Field()]
    activity_subgroup: Annotated[ActivityHierarchySimpleModel, Field()]
    activity_group: Annotated[ActivityHierarchySimpleModel, Field()]


class ActivityInstanceGrouping(ActivityGrouping):
    activity_uid: Annotated[str, Field()]


class ActivityInstance(ActivityBase):
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None

    @classmethod
    def from_activity_ar(
        cls,
        activity_ar: ActivityInstanceAR,
        find_activity_hierarchy_by_uid: Callable[[str], ActivityAR | None],
        find_activity_subgroup_by_uid: Callable[[str], ActivitySubGroupAR | None],
        find_activity_group_by_uid: Callable[[str], ActivityGroupAR | None],
    ) -> Self:
        activity_items = []
        for activity_item in activity_ar.concept_vo.activity_items:
            ct_terms = []
            unit_definitions = []
            odm_forms = []
            odm_item_groups = []
            odm_items = []
            for unit in activity_item.unit_definitions:
                unit_definitions.append(
                    CompactUnitDefinition(
                        uid=unit.uid, name=unit.name, dimension_name=unit.dimension_name
                    )
                )
            unit_definitions.sort(key=lambda x: x.uid)
            for term in activity_item.ct_terms:
                ct_terms.append(CompactCTTerm(uid=term.uid, name=term.name))
            ct_terms.sort(key=lambda x: x.uid)
            for odm_form in activity_item.odm_forms:
                odm_forms.append(
                    CompactOdmForm(
                        uid=odm_form.uid, oid=odm_form.oid, name=odm_form.name
                    )
                )
            odm_forms.sort(key=lambda x: x.uid)
            for odm_item_group in activity_item.odm_item_groups:
                odm_item_groups.append(
                    CompactOdmItemGroup(
                        uid=odm_item_group.uid,
                        oid=odm_item_group.oid,
                        name=odm_item_group.name,
                    )
                )
            odm_item_groups.sort(key=lambda x: x.uid)
            for odm_item in activity_item.odm_items:
                odm_items.append(
                    CompactOdmItem(
                        uid=odm_item.uid, oid=odm_item.oid, name=odm_item.name
                    )
                )
            odm_items.sort(key=lambda x: x.uid)

            activity_items.append(
                ActivityItem(
                    activity_item_class=CompactActivityItemClass(
                        uid=activity_item.activity_item_class_uid,
                        name=activity_item.activity_item_class_name,
                    ),
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    odm_forms=odm_forms,
                    odm_item_groups=odm_item_groups,
                    odm_items=odm_items,
                )
            )

        activity_groupings = []
        for activity_grouping in activity_ar.concept_vo.activity_groupings:
            if activity_grouping.activity_name:
                # Activity name is there, it means we are building for a GET query
                translation = ActivityInstanceHierarchySimpleModel(
                    activity_group=ActivityHierarchySimpleModel(
                        uid=activity_grouping.activity_group_uid,
                        name=activity_grouping.activity_group_name,
                    ),
                    activity_subgroup=ActivityHierarchySimpleModel(
                        uid=activity_grouping.activity_subgroup_uid,
                        name=activity_grouping.activity_subgroup_name,
                    ),
                    activity=ActivityHierarchySimpleModel(
                        uid=activity_grouping.activity_uid,
                        name=activity_grouping.activity_name,
                    ),
                )
            else:
                translation = ActivityInstanceHierarchySimpleModel(
                    activity_group=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_group_uid,
                        find_activity_by_uid=find_activity_group_by_uid,
                        version=activity_grouping.activity_group_version,
                    ),
                    activity_subgroup=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_subgroup_uid,
                        find_activity_by_uid=find_activity_subgroup_by_uid,
                        version=activity_grouping.activity_subgroup_version,
                    ),
                    activity=ActivityHierarchySimpleModel.from_activity_uid(
                        uid=activity_grouping.activity_uid,
                        find_activity_by_uid=find_activity_hierarchy_by_uid,
                        version=activity_grouping.activity_version,
                    ),
                )
            activity_groupings.append(translation)

        return cls(
            uid=activity_ar.uid,
            nci_concept_id=activity_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_ar.concept_vo.nci_concept_name,
            name=activity_ar.name,
            name_sentence_case=activity_ar.concept_vo.name_sentence_case,
            definition=activity_ar.concept_vo.definition,
            abbreviation=activity_ar.concept_vo.abbreviation,
            topic_code=activity_ar.concept_vo.topic_code,
            is_research_lab=activity_ar.concept_vo.is_research_lab,
            molecular_weight=activity_ar.concept_vo.molecular_weight,
            adam_param_code=activity_ar.concept_vo.adam_param_code,
            is_required_for_activity=activity_ar.concept_vo.is_required_for_activity,
            is_default_selected_for_activity=activity_ar.concept_vo.is_default_selected_for_activity,
            is_data_sharing=activity_ar.concept_vo.is_data_sharing,
            is_legacy_usage=activity_ar.concept_vo.is_legacy_usage,
            is_derived=activity_ar.concept_vo.is_derived,
            legacy_description=activity_ar.concept_vo.legacy_description,
            activity_groupings=activity_groupings,
            activity_name=activity_ar.concept_vo.activity_name,
            activity_instance_class=CompactActivityInstanceClass(
                uid=activity_ar.concept_vo.activity_instance_class_uid,
                name=activity_ar.concept_vo.activity_instance_class_name,
            ),
            activity_items=activity_items,
            library_name=Library.from_library_vo(activity_ar.library).name,
            start_date=activity_ar.item_metadata.start_date,
            end_date=activity_ar.item_metadata.end_date,
            status=activity_ar.item_metadata.status.value,
            version=activity_ar.item_metadata.version,
            change_description=activity_ar.item_metadata.change_description,
            author_username=activity_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_ar.get_possible_actions()]
            ),
        )

    @classmethod
    def from_activity_instance_ar_objects(
        cls, activity_instance_ar: ActivityInstanceAR
    ) -> Self:
        activity_items = []
        for activity_item in activity_instance_ar.concept_vo.activity_items:
            unit_definitions = sorted(
                [
                    CompactUnitDefinition(uid=unit.uid, name=unit.name)
                    for unit in activity_item.unit_definitions
                ],
                key=lambda x: x.uid,
            )

            ct_terms = sorted(
                [
                    CompactCTTerm(uid=term.uid, name=term.name)
                    for term in activity_item.ct_terms
                ],
                key=lambda x: x.uid,
            )

            odm_forms = sorted(
                [
                    CompactOdmForm(
                        uid=odm_form.uid, oid=odm_form.oid, name=odm_form.name
                    )
                    for odm_form in activity_item.odm_forms
                ],
                key=lambda x: x.uid,
            )

            odm_item_groups = sorted(
                [
                    CompactOdmItemGroup(
                        uid=odm_item_group.uid,
                        oid=odm_item_group.oid,
                        name=odm_item_group.name,
                    )
                    for odm_item_group in activity_item.odm_item_groups
                ],
                key=lambda x: x.uid,
            )

            odm_items = sorted(
                [
                    CompactOdmItem(
                        uid=odm_item.uid, oid=odm_item.oid, name=odm_item.name
                    )
                    for odm_item in activity_item.odm_items
                ],
                key=lambda x: x.uid,
            )

            activity_items.append(
                ActivityItem(
                    activity_item_class=CompactActivityItemClass(
                        uid=activity_item.activity_item_class_uid,
                        name=activity_item.activity_item_class_name,
                    ),
                    ct_terms=ct_terms,
                    unit_definitions=unit_definitions,
                    is_adam_param_specific=activity_item.is_adam_param_specific,
                    odm_forms=odm_forms,
                    odm_item_groups=odm_item_groups,
                    odm_items=odm_items,
                )
            )

        activity_instance_groupings = [
            ActivityInstanceHierarchySimpleModel(
                activity_group=ActivityHierarchySimpleModel(
                    uid=activity_instance_grouping_vo.activity_group_uid,
                    name=activity_instance_grouping_vo.activity_group_name,
                ),
                activity_subgroup=ActivityHierarchySimpleModel(
                    uid=activity_instance_grouping_vo.activity_subgroup_uid,
                    name=activity_instance_grouping_vo.activity_subgroup_name,
                ),
                activity=ActivityHierarchySimpleModel(
                    uid=activity_instance_grouping_vo.activity_uid,
                    name=activity_instance_grouping_vo.activity_name,
                ),
            )
            for activity_instance_grouping_vo in activity_instance_ar.concept_vo.activity_groupings
        ]

        return cls(
            uid=activity_instance_ar.uid,
            nci_concept_id=activity_instance_ar.concept_vo.nci_concept_id,
            nci_concept_name=activity_instance_ar.concept_vo.nci_concept_name,
            name=activity_instance_ar.name,
            name_sentence_case=activity_instance_ar.concept_vo.name_sentence_case,
            definition=activity_instance_ar.concept_vo.definition,
            abbreviation=activity_instance_ar.concept_vo.abbreviation,
            topic_code=activity_instance_ar.concept_vo.topic_code,
            is_research_lab=activity_instance_ar.concept_vo.is_research_lab,
            molecular_weight=activity_instance_ar.concept_vo.molecular_weight,
            adam_param_code=activity_instance_ar.concept_vo.adam_param_code,
            is_required_for_activity=activity_instance_ar.concept_vo.is_required_for_activity,
            is_default_selected_for_activity=activity_instance_ar.concept_vo.is_default_selected_for_activity,
            is_data_sharing=activity_instance_ar.concept_vo.is_data_sharing,
            is_legacy_usage=activity_instance_ar.concept_vo.is_legacy_usage,
            is_derived=activity_instance_ar.concept_vo.is_derived,
            legacy_description=activity_instance_ar.concept_vo.legacy_description,
            activity_groupings=sorted(
                activity_instance_groupings,
                key=lambda item: (
                    item.activity_subgroup.name,
                    item.activity_group.name,
                    item.activity.name,
                ),
            ),
            activity_name=activity_instance_ar.concept_vo.activity_name,
            activity_instance_class=CompactActivityInstanceClass(
                uid=activity_instance_ar.concept_vo.activity_instance_class_uid,
                name=activity_instance_ar.concept_vo.activity_instance_class_name,
            ),
            activity_items=activity_items,
            library_name=Library.from_library_vo(activity_instance_ar.library).name,
            start_date=activity_instance_ar.item_metadata.start_date,
            end_date=activity_instance_ar.item_metadata.end_date,
            status=activity_instance_ar.item_metadata.status.value,
            version=activity_instance_ar.item_metadata.version,
            change_description=activity_instance_ar.item_metadata.change_description,
            author_username=activity_instance_ar.item_metadata.author_username,
            possible_actions=sorted(
                [_.value for _ in activity_instance_ar.get_possible_actions()]
            ),
        )

    topic_code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    adam_param_code: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_research_lab: Annotated[bool, Field()] = False
    molecular_weight: Annotated[
        float | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_required_for_activity: Annotated[bool, Field()] = False
    is_default_selected_for_activity: Annotated[bool, Field()] = False
    is_data_sharing: Annotated[bool, Field()] = False
    is_legacy_usage: Annotated[bool, Field()] = False
    is_derived: Annotated[bool, Field()] = False
    legacy_description: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_groupings: Annotated[
        list[ActivityInstanceHierarchySimpleModel] | None, Field()
    ]
    activity_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    activity_instance_class: Annotated[
        CompactActivityInstanceClass,
        Field(description="The uid and the name of the linked activity instance class"),
    ]
    activity_items: Annotated[
        list[ActivityItem] | None,
        Field(
            description="List of activity items",
        ),
    ]
    start_date: Annotated[datetime | None, Field()]
    end_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    status: Annotated[str | None, Field()]
    version: Annotated[str | None, Field()]
    change_description: Annotated[str | None, Field()]
    author_username: Annotated[
        str | None,
        Field(
            json_schema_extra={"nullable": True},
        ),
    ] = None
    possible_actions: Annotated[
        list[str] | None,
        Field(
            description=(
                "Holds those actions that can be performed on the ActivityInstances. "
                "Actions are: 'approve', 'edit', 'new_version'."
            ),
        ),
    ]


class ActivityInstanceCreateInput(ExtendedConceptPostInput):
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    topic_code: Annotated[str | None, Field(min_length=1)] = None
    is_research_lab: Annotated[bool, Field()] = False
    molecular_weight: Annotated[float | None, Field()] = None
    adam_param_code: Annotated[str | None, Field(min_length=1)] = None
    is_required_for_activity: Annotated[bool, Field()] = False
    is_default_selected_for_activity: Annotated[bool, Field()] = False
    is_data_sharing: Annotated[bool, Field()] = False
    is_legacy_usage: Annotated[bool, Field()] = False
    is_derived: Annotated[bool, Field()] = False
    legacy_description: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: Annotated[list[ActivityInstanceGrouping] | None, Field()] = None
    activity_instance_class_uid: Annotated[str, Field(min_length=1)]
    activity_items: Annotated[list[ActivityItemCreateInput] | None, Field()] = None
    library_name: Annotated[str, Field(min_length=1)]


class ActivityInstancePreviewInput(ActivityInstanceCreateInput):
    name: Annotated[
        str | None,
        Field(
            description="The name or the actual value. E.g. 'Systolic Blood Pressure', 'Body Temperature', 'Metformin', ...",
            min_length=1,
        ),
    ] = None


class ActivityInstanceEditInput(ExtendedConceptPatchInput):
    nci_concept_id: Annotated[str | None, Field(min_length=1)] = None
    nci_concept_name: Annotated[str | None, Field(min_length=1)] = None
    topic_code: Annotated[str | None, Field(min_length=1)] = None
    is_research_lab: Annotated[bool | None, Field()] = None
    molecular_weight: Annotated[float | None, Field()] = None
    adam_param_code: Annotated[str | None, Field(min_length=1)] = None
    is_required_for_activity: Annotated[bool | None, Field()] = None
    is_default_selected_for_activity: Annotated[bool | None, Field()] = None
    is_data_sharing: Annotated[bool | None, Field()] = None
    is_legacy_usage: Annotated[bool | None, Field()] = None
    is_derived: Annotated[bool | None, Field()] = None
    legacy_description: Annotated[str | None, Field(min_length=1)] = None
    activity_instance_class_uid: Annotated[str | None, Field(min_length=1)] = None
    activity_groupings: Annotated[list[ActivityInstanceGrouping] | None, Field()] = None
    activity_items: Annotated[list[ActivityItemCreateInput] | None, Field()] = None
    change_description: Annotated[str, Field(min_length=1)]


class ActivityInstanceVersion(ActivityInstance):
    """
    Class for storing ActivityInstance and calculation of differences
    """

    changes: list[str] = Field(description=CHANGES_FIELD_DESC, default_factory=list)


class SimpleActivity(BaseModel):
    uid: Annotated[str, Field()]
    nci_concept_id: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    nci_concept_name: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    synonyms: Annotated[list[str], Field()]
    is_data_collected: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether data is collected for this activity",
        ),
    ] = False
    is_multiple_selection_allowed: Annotated[
        bool,
        Field(
            description="Boolean flag indicating whether multiple selections are allowed for this activity",
        ),
    ] = True
    library_name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    status: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None


class SimpleActivityItemClass(BaseModel):
    name: Annotated[str, Field()]
    order: Annotated[int, Field()]
    role_name: Annotated[str, Field()]
    data_type_name: Annotated[str, Field()]


class SimplifiedActivityItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ct_terms: list[LibraryItem] = Field(default_factory=list)
    unit_definitions: list[CompactUnitDefinition] = Field(default_factory=list)
    activity_item_class: Annotated[SimpleActivityItemClass, Field()]
    is_adam_param_specific: Annotated[bool, Field()]
    odm_forms: list[CompactOdmForm] = Field(default_factory=list)
    odm_item_groups: list[CompactOdmItemGroup] = Field(default_factory=list)
    odm_items: list[CompactOdmItem] = Field(default_factory=list)


class SimpleActivityInstanceGrouping(SimpleActivityGrouping):
    activity: Annotated[SimpleActivity, Field()]


class ActivityInstanceOverview(BaseModel):
    activity_groupings: Annotated[list[SimpleActivityInstanceGrouping], Field()]
    activity_instance: Annotated[SimpleActivityInstance, Field()]
    activity_items: Annotated[list[SimplifiedActivityItem], Field()]
    all_versions: Annotated[list[str], Field()]

    @classmethod
    def from_repository_input(cls, overview: dict[str, Any]):
        activity_items = []
        for activity_item in overview.get("activity_items"):
            units = sorted(
                [
                    CompactUnitDefinition(
                        name=unit.get("name"),
                        uid=unit.get("uid"),
                        dimension_name=unit.get("dimension_name"),
                    )
                    for unit in activity_item.get("unit_definitions", {})
                ],
                key=lambda x: x.uid,
            )
            terms = sorted(
                [
                    LibraryItem(name=term.get("name"), uid=term.get("uid"))
                    for term in activity_item.get("ct_terms", {})
                ],
                key=lambda x: x.uid,
            )
            odm_forms = sorted(
                [
                    CompactOdmForm(
                        uid=odm_form.get("uid"),
                        oid=odm_form.get("oid"),
                        name=odm_form.get("name"),
                    )
                    for odm_form in activity_item.get("odm_forms", [])
                ],
                key=lambda x: x.uid,
            )
            odm_item_groups = sorted(
                [
                    CompactOdmItemGroup(
                        uid=odm_item_group.get("uid"),
                        oid=odm_item_group.get("oid"),
                        name=odm_item_group.get("name"),
                    )
                    for odm_item_group in activity_item.get("odm_item_groups", [])
                ],
                key=lambda x: x.uid,
            )
            odm_items = sorted(
                [
                    CompactOdmItem(
                        uid=odm_item.get("uid"),
                        oid=odm_item.get("oid"),
                        name=odm_item.get("name"),
                    )
                    for odm_item in activity_item.get("odm_items", [])
                ],
                key=lambda x: x.uid,
            )
            # Extract activity_item_class handling Neo4j node format
            aic = activity_item.get("activity_item_class", {})
            if "properties" in aic:
                aic_name = aic["properties"].get("name", "")
                aic_order = aic["properties"].get("order", 0)
                if isinstance(aic_order, dict):
                    aic_order = aic_order.get("low", 0)
            else:
                aic_name = aic.get("name", "")
                aic_order = aic.get("order", 0)

            activity_items.append(
                SimplifiedActivityItem(
                    ct_terms=terms,
                    unit_definitions=units,
                    odm_forms=odm_forms,
                    odm_item_groups=odm_item_groups,
                    odm_items=odm_items,
                    activity_item_class=SimpleActivityItemClass(
                        name=aic_name,
                        order=aic_order,
                        role_name=activity_item.get("activity_item_class_role"),
                        data_type_name=activity_item.get(
                            "activity_item_class_data_type"
                        ),
                    ),
                    is_adam_param_specific=activity_item.get(
                        "is_adam_param_specific", False
                    ),
                )
            )

        return cls(
            activity_groupings=[
                SimpleActivityInstanceGrouping(
                    activity=SimpleActivity(
                        uid=activity_grouping.get("uid"),
                        name=activity_grouping.get("activity_value").get("name"),
                        definition=activity_grouping.get("activity_value").get(
                            "definition"
                        ),
                        nci_concept_id=activity_grouping.get("activity_value").get(
                            "nci_concept_id"
                        ),
                        nci_concept_name=activity_grouping.get("activity_value").get(
                            "nci_concept_name"
                        ),
                        synonyms=activity_grouping.get("activity_value").get(
                            "synonyms", []
                        ),
                        is_data_collected=activity_grouping.get("activity_value").get(
                            "is_data_collected", False
                        ),
                        is_multiple_selection_allowed=activity_grouping.get(
                            "activity_value"
                        ).get("is_multiple_selection_allowed", True),
                        library_name=activity_grouping.get("activity_library_name"),
                        version=(activity_grouping.get("version") or {}).get("version"),
                        status=(activity_grouping.get("version") or {}).get("status"),
                    ),
                    activity_group=SimpleActivityGroup(
                        uid=activity_grouping.get("activity_group_uid"),
                        name=activity_grouping.get("activity_group_value").get("name"),
                        definition=activity_grouping.get("activity_group_value").get(
                            "definition"
                        ),
                        version=(
                            activity_grouping.get("activity_group_version") or {}
                        ).get("version"),
                        status=(
                            activity_grouping.get("activity_group_version") or {}
                        ).get("status"),
                    ),
                    activity_subgroup=SimpleActivitySubGroup(
                        uid=activity_grouping.get("activity_subgroup_uid"),
                        name=activity_grouping.get("activity_subgroup_value").get(
                            "name"
                        ),
                        definition=activity_grouping.get("activity_subgroup_value").get(
                            "definition"
                        ),
                        version=(
                            activity_grouping.get("activity_subgroup_version") or {}
                        ).get("version"),
                        status=(
                            activity_grouping.get("activity_subgroup_version") or {}
                        ).get("status"),
                    ),
                )
                for activity_grouping in overview.get("hierarchy")
            ],
            activity_instance=SimpleActivityInstance(
                uid=overview.get("activity_instance_root").get("uid"),
                name=overview.get("activity_instance_value").get("name"),
                name_sentence_case=overview.get("activity_instance_value").get(
                    "name_sentence_case"
                ),
                abbreviation=overview.get("activity_instance_value").get(
                    "abbreviation"
                ),
                definition=overview.get("activity_instance_value").get("definition"),
                nci_concept_id=overview.get("activity_instance_value").get(
                    "nci_concept_id"
                ),
                nci_concept_name=overview.get("activity_instance_value").get(
                    "nci_concept_name"
                ),
                adam_param_code=overview.get("activity_instance_value").get(
                    "adam_param_code"
                ),
                is_required_for_activity=overview.get("activity_instance_value").get(
                    "is_required_for_activity", False
                ),
                is_default_selected_for_activity=overview.get(
                    "activity_instance_value"
                ).get("is_default_selected_for_activity", False),
                is_data_sharing=overview.get("activity_instance_value").get(
                    "is_data_sharing", False
                ),
                is_legacy_usage=overview.get("activity_instance_value").get(
                    "is_legacy_usage", False
                ),
                is_derived=overview.get("activity_instance_value").get(
                    "is_derived", False
                ),
                topic_code=overview.get("activity_instance_value").get("topic_code"),
                is_research_lab=overview.get("activity_instance_value").get(
                    "is_research_lab", False
                ),
                molecular_weight=overview.get("activity_instance_value").get(
                    "molecular_weight"
                ),
                library_name=overview.get("instance_library_name"),
                activity_instance_class=SimpleActivityInstanceClass(
                    name=overview.get("activity_instance_class").get("name")
                ),
                status=overview.get("has_version", {}).get("status"),
                version=overview.get("has_version", {}).get("version"),
                start_date=convert_to_datetime(
                    overview.get("has_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    overview.get("has_version", {}).get("end_date")
                ),
            ),
            activity_items=activity_items,
            all_versions=overview.get("all_versions"),
        )


class ActivityInstanceDetail(BaseModel):
    """Model for activity instance detail information with pagination support."""

    uid: Annotated[str, Field()]
    name: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = None
    definition: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    abbreviation: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    version: Annotated[str, Field()]
    status: Annotated[str, Field()]
    activity_instance_class: Annotated[SimpleActivityInstanceClass | None, Field()] = (
        None
    )
    start_date: Annotated[
        datetime | None, Field(json_schema_extra={"nullable": True})
    ] = None
    is_required_for_activity: Annotated[bool, Field()] = False
    is_default_selected_for_activity: Annotated[bool, Field()] = False
    topic_code: Annotated[str | None, Field(json_schema_extra={"nullable": True})] = (
        None
    )
    adam_param_code: Annotated[
        str | None, Field(json_schema_extra={"nullable": True})
    ] = None
    children: Annotated[list[dict[Any, Any]] | None, Field()] = None


class ActivityInstancePaginatedResponse(BaseModel):
    """Paginated response for activity instances."""

    items: list[ActivityInstanceDetail]
    total: int
    page: int
    page_size: int

    @classmethod
    def from_repository_input(cls, overview: dict[str, Any]):
        activity_items = []
        for activity_item in overview.get("activity_items"):
            units = sorted(
                [
                    CompactUnitDefinition(
                        name=unit.get("name"),
                        uid=unit.get("uid"),
                        dimension_name=unit.get("dimension_name"),
                    )
                    for unit in activity_item.get("unit_definitions", {})
                ],
                key=lambda x: x.uid,
            )
            terms = sorted(
                [
                    LibraryItem(name=term.get("name"), uid=term.get("uid"))
                    for term in activity_item.get("ct_terms", {})
                ],
                key=lambda x: x.uid,
            )

            odm_forms = sorted(
                [
                    CompactOdmForm(
                        uid=odm_form.get("uid"),
                        oid=odm_form.get("oid"),
                        name=odm_form.get("name"),
                    )
                    for odm_form in activity_item.get("odm_forms", [])
                ],
                key=lambda x: x.uid,
            )
            odm_item_groups = sorted(
                [
                    CompactOdmItemGroup(
                        uid=odm_item_group.get("uid"),
                        oid=odm_item_group.get("oid"),
                        name=odm_item_group.get("name"),
                    )
                    for odm_item_group in activity_item.get("odm_item_groups", [])
                ],
                key=lambda x: x.uid,
            )
            odm_items = sorted(
                [
                    CompactOdmItem(
                        uid=odm_item.get("uid"),
                        oid=odm_item.get("oid"),
                        name=odm_item.get("name"),
                    )
                    for odm_item in activity_item.get("odm_items", [])
                ],
                key=lambda x: x.uid,
            )
            # Extract activity_item_class handling Neo4j node format
            aic = activity_item.get("activity_item_class", {})
            if "properties" in aic:
                aic_name = aic["properties"].get("name", "")
                aic_order = aic["properties"].get("order", 0)
                if isinstance(aic_order, dict):
                    aic_order = aic_order.get("low", 0)
            else:
                aic_name = aic.get("name", "")
                aic_order = aic.get("order", 0)

            activity_items.append(
                SimplifiedActivityItem(
                    ct_terms=terms,
                    unit_definitions=units,
                    odm_forms=odm_forms,
                    odm_item_groups=odm_item_groups,
                    odm_items=odm_items,
                    activity_item_class=SimpleActivityItemClass(
                        name=aic_name,
                        order=aic_order,
                        role_name=activity_item.get("activity_item_class_role"),
                        data_type_name=activity_item.get(
                            "activity_item_class_data_type"
                        ),
                    ),
                    is_adam_param_specific=activity_item.get(
                        "is_adam_param_specific", False
                    ),
                )
            )

        return cls(
            activity_groupings=[
                SimpleActivityInstanceGrouping(
                    activity=SimpleActivity(
                        uid=activity_grouping.get("uid"),
                        name=activity_grouping.get("activity_value").get("name"),
                        definition=activity_grouping.get("activity_value").get(
                            "definition"
                        ),
                        nci_concept_id=activity_grouping.get("activity_value").get(
                            "nci_concept_id"
                        ),
                        nci_concept_name=activity_grouping.get("activity_value").get(
                            "nci_concept_name"
                        ),
                        synonyms=activity_grouping.get("activity_value").get(
                            "synonyms", []
                        ),
                        is_data_collected=activity_grouping.get("activity_value").get(
                            "is_data_collected", False
                        ),
                        is_multiple_selection_allowed=activity_grouping.get(
                            "activity_value"
                        ).get("is_multiple_selection_allowed", True),
                        library_name=activity_grouping.get("activity_library_name"),
                        version=(activity_grouping.get("version") or {}).get("version"),
                        status=(activity_grouping.get("version") or {}).get("status"),
                    ),
                    activity_group=SimpleActivityGroup(
                        uid=activity_grouping.get("activity_group_uid"),
                        name=activity_grouping.get("activity_group_value").get("name"),
                        definition=activity_grouping.get("activity_group_value").get(
                            "definition"
                        ),
                        version=(
                            activity_grouping.get("activity_group_version") or {}
                        ).get("version"),
                        status=(
                            activity_grouping.get("activity_group_version") or {}
                        ).get("status"),
                    ),
                    activity_subgroup=SimpleActivitySubGroup(
                        uid=activity_grouping.get("activity_subgroup_uid"),
                        name=activity_grouping.get("activity_subgroup_value").get(
                            "name"
                        ),
                        definition=activity_grouping.get("activity_subgroup_value").get(
                            "definition"
                        ),
                        version=(
                            activity_grouping.get("activity_subgroup_version") or {}
                        ).get("version"),
                        status=(
                            activity_grouping.get("activity_subgroup_version") or {}
                        ).get("status"),
                    ),
                )
                for activity_grouping in overview.get("hierarchy")
            ],
            activity_instance=SimpleActivityInstance(
                uid=overview.get("activity_instance_root").get("uid"),
                name=overview.get("activity_instance_value").get("name"),
                name_sentence_case=overview.get("activity_instance_value").get(
                    "name_sentence_case"
                ),
                abbreviation=overview.get("activity_instance_value").get(
                    "abbreviation"
                ),
                definition=overview.get("activity_instance_value").get("definition"),
                nci_concept_id=overview.get("activity_instance_value").get(
                    "nci_concept_id"
                ),
                nci_concept_name=overview.get("activity_instance_value").get(
                    "nci_concept_name"
                ),
                adam_param_code=overview.get("activity_instance_value").get(
                    "adam_param_code"
                ),
                is_required_for_activity=overview.get("activity_instance_value").get(
                    "is_required_for_activity", False
                ),
                is_default_selected_for_activity=overview.get(
                    "activity_instance_value"
                ).get("is_default_selected_for_activity", False),
                is_data_sharing=overview.get("activity_instance_value").get(
                    "is_data_sharing", False
                ),
                is_legacy_usage=overview.get("activity_instance_value").get(
                    "is_legacy_usage", False
                ),
                is_derived=overview.get("activity_instance_value").get(
                    "is_derived", False
                ),
                topic_code=overview.get("activity_instance_value").get("topic_code"),
                is_research_lab=overview.get("activity_instance_value").get(
                    "is_research_lab", False
                ),
                molecular_weight=overview.get("activity_instance_value").get(
                    "molecular_weight"
                ),
                library_name=overview.get("instance_library_name"),
                activity_instance_class=SimpleActivityInstanceClass(
                    name=overview.get("activity_instance_class").get("name")
                ),
                status=overview.get("has_version", {}).get("status"),
                version=overview.get("has_version", {}).get("version"),
                start_date=convert_to_datetime(
                    overview.get("has_version", {}).get("start_date")
                ),
                end_date=convert_to_datetime(
                    overview.get("has_version", {}).get("end_date")
                ),
            ),
            activity_items=activity_items,
            all_versions=overview.get("all_versions"),
        )
