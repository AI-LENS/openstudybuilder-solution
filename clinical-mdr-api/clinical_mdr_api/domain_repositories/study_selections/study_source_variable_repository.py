import datetime

from clinical_mdr_api.domain_repositories._utils.helpers import (
    acquire_write_lock_study_value,
)
from clinical_mdr_api.domain_repositories.models.study import StudyRoot, StudyValue
from clinical_mdr_api.domain_repositories.models.study_audit_trail import Create, Edit
from clinical_mdr_api.domain_repositories.models.study_selections import (
    StudySourceVariable as StudySourceVariableNeomodel,
)
from clinical_mdr_api.domains.enums import StudySourceVariableEnum
from clinical_mdr_api.models.study_selections.study_selection import (
    StudySourceVariableInput,
)
from common import exceptions


class StudySourceVariableRepository:

    def get_study_source_variable(
        self,
        study_uid: str,
        study_value_version: str | None = None,
        for_update: bool = False,
    ) -> StudySourceVariableNeomodel | None:
        if for_update:
            acquire_write_lock_study_value(study_uid)

        if study_value_version:
            filters = {
                "has_study_source_variable__has_version__uid": study_uid,
                "has_study_source_variable__has_version|version": study_value_version,
            }
        else:
            filters = {
                "has_study_source_variable__latest_value__uid": study_uid,
            }

        nodes = (
            StudySourceVariableNeomodel.nodes.fetch_relations(
                "has_after__audit_trail",
            )
            .filter(**filters)
            .resolve_subgraph()
        )
        exceptions.BusinessLogicException.raise_if(
            len(nodes) > 1,
            msg=f"Found more than one StudySourceVariable node for Study with UID '{study_uid}'.",
        )
        return nodes[0] if len(nodes) > 0 else None

    def post_study_source_variable(
        self,
        study_uid: str,
        study_source_variable_input: StudySourceVariableInput,
        author_id: str,
    ) -> StudySourceVariableNeomodel:
        """Creates StudySourceVariable node if none are present"""

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value: StudyValue = study_root.latest_value.single()

        source_variable: StudySourceVariableEnum | None = (
            study_source_variable_input.source_variable
        )
        study_source_variable_node = StudySourceVariableNeomodel.create(
            {
                "source_variable": source_variable.value if source_variable else None,
                "source_variable_description": study_source_variable_input.source_variable_description,
            }
        )[0]
        latest_study_value.has_study_source_variable.connect(study_source_variable_node)

        action = Create(
            date=datetime.datetime.now(datetime.timezone.utc),
            author_id=author_id,
        )
        action.save()
        action.has_after.connect(study_source_variable_node)
        study_root.audit_trail.connect(action)

        return self.get_study_source_variable(study_uid=study_uid)

    def edit_study_source_variable(
        self,
        study_uid: str,
        study_source_variable_input: StudySourceVariableInput,
        previous_node: StudySourceVariableNeomodel,
        author_id: str,
    ) -> StudySourceVariableNeomodel:
        """Replaces StudySourceVariable node"""

        study_root = StudyRoot.nodes.get(uid=study_uid)
        latest_study_value: StudyValue = study_root.latest_value.single()

        # disconnect the previous version from StudyValue
        latest_study_value.has_study_source_variable.disconnect(previous_node)

        source_variable: StudySourceVariableEnum | None = (
            study_source_variable_input.source_variable
        )
        study_source_variable_node = StudySourceVariableNeomodel.create(
            {
                "source_variable": source_variable.value if source_variable else None,
                "source_variable_description": study_source_variable_input.source_variable_description,
            }
        )[0]
        latest_study_value.has_study_source_variable.connect(study_source_variable_node)

        action = Edit(
            date=datetime.datetime.now(datetime.timezone.utc),
            author_id=author_id,
        )
        action.save()
        action.has_before.connect(previous_node)
        action.has_after.connect(study_source_variable_node)
        study_root.audit_trail.connect(action)

        return self.get_study_source_variable(study_uid=study_uid)
