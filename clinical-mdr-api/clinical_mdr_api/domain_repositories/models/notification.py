from neomodel import IntegerProperty, StringProperty

from clinical_mdr_api.domain_repositories.models.generic import (
    ClinicalMdrNode,
    ZonedDateTimeProperty,
)


class Notification(ClinicalMdrNode):
    sn = IntegerProperty(unique_index=True)
    title = StringProperty()
    description = StringProperty()
    notification_type = StringProperty()
    started_at = ZonedDateTimeProperty()
    ended_at = ZonedDateTimeProperty()
    published_at = ZonedDateTimeProperty()
