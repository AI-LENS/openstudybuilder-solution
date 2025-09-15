import datetime
from dataclasses import dataclass


@dataclass
class StudyDesignCellVO:
    study_uid: str
    study_epoch_uid: str
    study_element_uid: str
    transition_rule: str | None
    order: int

    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    author_username: str | None = None

    uid: str | None = None
    study_element_name: str | None = None
    study_epoch_name: str | None = None
    study_arm_uid: str | None = None
    study_arm_name: str | None = None
    study_branch_arm_uid: str | None = None
    study_branch_arm_name: str | None = None

    def edit_core_properties(
        self,
        order: int,
        transition_rule: str,
        study_epoch_uid: str,
        study_element_uid: str | None,
        study_arm_uid: str | None,
        study_branch_arm_uid: str | None,
    ):
        self.study_epoch_uid = study_epoch_uid
        self.study_element_uid = study_element_uid  # type: ignore[assignment]
        self.study_arm_uid = study_arm_uid
        self.study_branch_arm_uid = study_branch_arm_uid
        self.transition_rule = transition_rule
        self.order = order
