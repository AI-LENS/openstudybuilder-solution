import datetime
from dataclasses import dataclass, replace
from enum import Enum
from typing import Callable

from clinical_mdr_api.domains.study_selections import study_selection_base
from clinical_mdr_api.services.user_info import UserInfoService
from clinical_mdr_api.utils import normalize_string
from common.exceptions import AlreadyExistsException, ValidationException


class StudyActivityInstanceState(Enum):
    MISSING_SELECTION = "Missing selection"
    REQUIRED = "Required"
    DEFAULTED = "Defaulted"
    SUGGESTION = "Suggestion"
    NOT_REQUIRED = "Not required"


@dataclass(frozen=True)
class StudySelectionActivityInstanceVO(study_selection_base.StudySelectionBaseVO):
    """
    The StudySelectionActivityInstanceVO acts as the value object for a
    single selection between a study and an activity instance
    """

    study_uid: str
    study_selection_uid: str
    study_activity_uid: str
    activity_uid: str
    activity_name: str | None
    activity_version: str
    activity_instance_uid: str | None
    activity_instance_name: str | None
    activity_instance_version: str | None
    show_activity_instance_in_protocol_flowchart: bool
    keep_old_version: bool
    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str | None
    author_username: str | None = None
    accepted_version: bool = False
    study_activity_subgroup_uid: str | None = None
    activity_subgroup_uid: str | None = None
    activity_subgroup_name: str | None = None
    study_activity_group_uid: str | None = None
    activity_group_uid: str | None = None
    activity_group_name: str | None = None
    study_soa_group_uid: str | None = None
    soa_group_term_uid: str | None = None
    soa_group_term_name: str | None = None

    @classmethod
    def from_input_values(
        cls,
        study_uid: str,
        author_id: str,
        study_activity_uid: str,
        author_username: str | None = None,
        activity_uid: str | None = None,
        activity_name: str | None = None,
        activity_version: str | None = None,
        activity_instance_uid: str | None = None,
        activity_instance_name: str | None = None,
        activity_instance_version: str | None = None,
        show_activity_instance_in_protocol_flowchart: bool | None = False,
        keep_old_version: bool | None = False,
        study_selection_uid: str | None = None,
        start_date: datetime.datetime | None = None,
        accepted_version: bool = False,
        generate_uid_callback: Callable[[], str] | None = None,
        study_activity_subgroup_uid: str | None = None,
        activity_subgroup_uid: str | None = None,
        activity_subgroup_name: str | None = None,
        study_activity_group_uid: str | None = None,
        activity_group_uid: str | None = None,
        activity_group_name: str | None = None,
        study_soa_group_uid: str | None = None,
        soa_group_term_uid: str | None = None,
        soa_group_term_name: str | None = None,
    ):
        if study_selection_uid is None:
            study_selection_uid = generate_uid_callback()

        if start_date is None:
            start_date = datetime.datetime.now(datetime.timezone.utc)

        return cls(
            study_uid=normalize_string(study_uid),
            study_activity_uid=normalize_string(study_activity_uid),
            activity_instance_uid=normalize_string(activity_instance_uid),
            activity_instance_name=normalize_string(activity_instance_name),
            activity_instance_version=normalize_string(activity_instance_version),
            activity_uid=normalize_string(activity_uid),
            activity_name=normalize_string(activity_name),
            activity_version=normalize_string(activity_version),
            show_activity_instance_in_protocol_flowchart=show_activity_instance_in_protocol_flowchart,
            keep_old_version=keep_old_version,
            start_date=start_date,
            study_selection_uid=normalize_string(study_selection_uid),
            author_id=normalize_string(author_id),
            author_username=(
                UserInfoService.get_author_username_from_id(author_id)
                if author_username is None
                else author_username
            ),
            accepted_version=accepted_version,
            study_activity_subgroup_uid=study_activity_subgroup_uid,
            activity_subgroup_uid=activity_subgroup_uid,
            activity_subgroup_name=activity_subgroup_name,
            study_activity_group_uid=study_activity_group_uid,
            activity_group_uid=activity_group_uid,
            activity_group_name=activity_group_name,
            study_soa_group_uid=study_soa_group_uid,
            soa_group_term_uid=soa_group_term_uid,
            soa_group_term_name=soa_group_term_name,
        )

    def validate(
        self,
        object_exist_callback: Callable[[str], bool] = (lambda _: True),
        ct_term_level_exist_callback: Callable[[str], bool] = (lambda _: True),
    ) -> None:
        # Checks if there exists an activity which is approved with activity_uid
        ValidationException.raise_if(
            self.activity_instance_uid
            and not object_exist_callback(normalize_string(self.activity_instance_uid)),
            msg=f"There is no approved Activity Instance with UID '{self.activity_instance_uid}'.",
        )

    def update_version(self, activity_instance_version: str):
        return replace(self, activity_instance_version=activity_instance_version)

    def update_keep_old_version(self, keep_old_version: bool):
        return replace(self, keep_old_version=keep_old_version)


@dataclass
class StudySelectionActivityInstanceAR(study_selection_base.StudySelectionBaseAR):
    """
    The StudySelectionActivityInstanceAR holds all the study activity instance
    selections for a given study, the aggregate root also, takes care
    of all operations changing the study selections for a study.

    * add more selections
    * remove selections
    * patch selection
    * delete selection
    """

    _object_type = "activity_instance"
    _object_uid_field = "activity_instance_uid"
    _object_name_field = "activity_instance_name"
    _order_field_name = ""

    def validate(self):
        objects = []
        for selection in self.study_objects_selection:
            object_uid = getattr(selection, self._object_uid_field)
            activity_uid = selection.activity_uid
            activity_subgroup_uid = selection.activity_subgroup_uid
            activity_group_uid = selection.activity_group_uid
            AlreadyExistsException.raise_if(
                (
                    object_uid,
                    activity_uid,
                    activity_subgroup_uid,
                    activity_group_uid,
                )
                in objects,
                msg=f"There is already a Study Activity Instance with UID '{object_uid}' linked to the Activity with UID '{activity_uid}'.",
            )
            objects.append(
                (object_uid, activity_uid, activity_subgroup_uid, activity_group_uid)
            )
