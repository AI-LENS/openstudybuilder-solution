import datetime
from dataclasses import dataclass


@dataclass
class StudyActivityScheduleVO:
    study_uid: str
    study_activity_uid: str
    study_activity_instance_uid: str | None
    study_visit_uid: str | None

    # Study selection Versioning
    start_date: datetime.datetime
    author_id: str
    author_username: str | None = None

    uid: str | None = None
