from clinical_mdr_api.domain_repositories.models.generic import (
    Library,
    VersionRelationship,
)
from clinical_mdr_api.domain_repositories.models.syntax import (
    ObjectivePreInstanceRoot,
    ObjectivePreInstanceValue,
    ObjectiveTemplateRoot,
)
from clinical_mdr_api.domain_repositories.syntax_instances.generic_syntax_instance_repository import (
    GenericSyntaxInstanceRepository,
)
from clinical_mdr_api.domains.syntax_pre_instances.objective_pre_instance import (
    ObjectivePreInstanceAR,
)
from clinical_mdr_api.domains.versioned_object_aggregate import LibraryVO
from clinical_mdr_api.models.controlled_terminologies.ct_term import (
    SimpleCTTermNameAndAttributes,
    SimpleTermAttributes,
    SimpleTermModel,
    SimpleTermName,
)


class ObjectivePreInstanceRepository(
    GenericSyntaxInstanceRepository[ObjectivePreInstanceAR]
):
    root_class = ObjectivePreInstanceRoot
    value_class = ObjectivePreInstanceValue
    template_class = ObjectiveTemplateRoot

    def _create_ar(
        self,
        root: ObjectivePreInstanceRoot,
        library: Library,
        relationship: VersionRelationship,
        value: ObjectivePreInstanceValue,
        study_count: int = 0,
        **kwargs,
    ):
        return ObjectivePreInstanceAR.from_repository_values(
            uid=root.uid,
            sequence_id=root.sequence_id,
            library=LibraryVO.from_input_values_2(
                library_name=library.name,
                is_library_editable_callback=lambda _: library.is_editable,
            ),
            item_metadata=self._library_item_metadata_vo_from_relation(relationship),
            template=self.get_template_vo(root, value, kwargs["instance_template"]),
            is_confirmatory_testing=root.is_confirmatory_testing,
            indications=sorted(
                [
                    SimpleTermModel(
                        term_uid=indication["term_uid"], name=indication["name"]
                    )
                    for indication in kwargs["indications"]
                    if indication["term_uid"]
                ],
                key=lambda x: x.term_uid,
            ),
            categories=sorted(
                [
                    SimpleCTTermNameAndAttributes(
                        term_uid=category["term_uid"],
                        name=SimpleTermName(
                            sponsor_preferred_name=category["name"],
                            sponsor_preferred_name_sentence_case=category[
                                "name_sentence_case"
                            ],
                        ),
                        attributes=SimpleTermAttributes(
                            code_submission_value=category["code_submission_value"],
                            nci_preferred_name=category["preferred_term"],
                        ),
                    )
                    for category in kwargs["categories"]
                    if category["term_uid"]
                ],
                key=lambda x: x.term_uid,
            ),
            study_count=study_count,
        )

    def _create(self, item: ObjectivePreInstanceAR) -> ObjectivePreInstanceAR:
        """
        This method calls the generic _create method, then extends it to add specific actions
        Specific actions are :
        * Attaching root node to indication nodes
        * Attaching root node to category nodes
        """
        root, item = super()._create(item)

        root.is_confirmatory_testing = item.is_confirmatory_testing
        self._db_save_node(root)

        for indication in item.indications or []:
            root.has_indication.connect(self._get_indication(indication.term_uid))
        for category in item.categories or []:
            root.has_category.connect(self._get_category(category.term_uid))

        return item
