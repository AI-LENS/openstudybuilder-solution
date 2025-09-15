import datetime
from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)

# pylint: disable=too-many-arguments


@dataclass(frozen=True)
class SponsorModelDatasetVariableVO:
    """
    The SponsorModelDatasetVariableVO acts as the value object for a single SponsorModelDatasetVariable value object
    """

    dataset_uid: str | None
    variable_uid: str | None
    sponsor_model_name: str | None
    sponsor_model_version_number: str

    is_basic_std: bool
    implemented_parent_dataset_class: str | None
    implemented_variable_class: str | None
    label: str | None
    order: int | None
    variable_type: str | None
    length: int | None
    display_format: str | None
    xml_datatype: str | None
    references_codelists: list[str] | None
    references_terms: list[str] | None
    core: str | None
    origin: str | None
    origin_type: str | None
    origin_source: str | None
    role: str | None
    term: str | None
    algorithm: str | None
    qualifiers: list[str] | None
    is_cdisc_std: bool
    comment: str | None
    ig_comment: str | None
    class_table: str | None
    class_column: str | None
    map_var_flag: str | None
    fixed_mapping: str | None
    include_in_raw: bool
    nn_internal: bool
    value_lvl_where_cols: str | None
    value_lvl_label_col: str | None
    value_lvl_collect_ct_val: str | None
    value_lvl_ct_codelist_id_col: str | None
    enrich_build_order: int | None
    enrich_rule: str | None
    target_data_model_catalogue: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        dataset_uid: str,
        variable_uid: str,
        sponsor_model_name: str,
        sponsor_model_version_number: str,
        is_basic_std: bool,
        implemented_parent_dataset_class: str | None,
        implemented_variable_class: str | None,
        label: str | None,
        order: int | None,
        variable_type: str | None,
        length: int | None,
        display_format: str | None,
        xml_datatype: str | None,
        references_codelists: list[str] | None,
        references_terms: list[str] | None,
        core: str | None,
        origin: str | None,
        origin_type: str | None,
        origin_source: str | None,
        role: str | None,
        term: str | None,
        algorithm: str | None,
        qualifiers: list[str] | None,
        is_cdisc_std: bool,
        comment: str | None,
        ig_comment: str | None,
        class_table: str | None,
        class_column: str | None,
        map_var_flag: str | None,
        fixed_mapping: str | None,
        include_in_raw: bool,
        nn_internal: bool,
        value_lvl_where_cols: str | None,
        value_lvl_label_col: str | None,
        value_lvl_collect_ct_val: str | None,
        value_lvl_ct_codelist_id_col: str | None,
        enrich_build_order: int | None,
        enrich_rule: str | None,
        target_data_model_catalogue: str | None = None,
    ) -> Self:
        sponsor_model_dataset_variable_vo = cls(
            dataset_uid=dataset_uid,
            variable_uid=variable_uid,
            sponsor_model_name=sponsor_model_name,
            sponsor_model_version_number=sponsor_model_version_number,
            is_basic_std=is_basic_std,
            implemented_parent_dataset_class=implemented_parent_dataset_class,
            implemented_variable_class=implemented_variable_class,
            label=label,
            order=order,
            variable_type=variable_type,
            length=length,
            display_format=display_format,
            xml_datatype=xml_datatype,
            references_codelists=references_codelists,
            references_terms=references_terms,
            core=core,
            origin=origin,
            origin_type=origin_type,
            origin_source=origin_source,
            role=role,
            term=term,
            algorithm=algorithm,
            qualifiers=qualifiers,
            is_cdisc_std=is_cdisc_std,
            comment=comment,
            ig_comment=ig_comment,
            class_table=class_table,
            class_column=class_column,
            map_var_flag=map_var_flag,
            fixed_mapping=fixed_mapping,
            include_in_raw=include_in_raw,
            nn_internal=nn_internal,
            value_lvl_where_cols=value_lvl_where_cols,
            value_lvl_label_col=value_lvl_label_col,
            value_lvl_collect_ct_val=value_lvl_collect_ct_val,
            value_lvl_ct_codelist_id_col=value_lvl_ct_codelist_id_col,
            enrich_build_order=enrich_build_order,
            enrich_rule=enrich_rule,
            target_data_model_catalogue=target_data_model_catalogue,
        )

        return sponsor_model_dataset_variable_vo


class SponsorModelDatasetVariableMetadataVO(LibraryItemMetadataVO):
    @property
    def version(self) -> str:
        return self._major_version

    # pylint: disable=arguments-renamed
    @classmethod
    def get_initial_item_metadata(cls, author_id: str, version: str) -> Self:
        return cls(
            _change_description="Approved version",
            _status=LibraryItemStatus.FINAL,
            _author_id=author_id,
            _start_date=datetime.datetime.now(datetime.timezone.utc),
            _end_date=None,
            _major_version=int(version),
            _minor_version=0,
        )


@dataclass
class SponsorModelDatasetVariableAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model variable aggregate for versioned sponsor models
    """

    _sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO

    @property
    def sponsor_model_dataset_variable_vo(self) -> SponsorModelDatasetVariableVO:
        return self._sponsor_model_dataset_variable_vo

    @sponsor_model_dataset_variable_vo.setter
    def sponsor_model_dataset_variable_vo(
        self, sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO
    ):
        self._sponsor_model_dataset_variable_vo = sponsor_model_dataset_variable_vo

    @property
    def name(self) -> str:
        return self._uid

    @classmethod
    def from_repository_values(
        cls,
        variable_uid: str,
        sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        sponsor_model_dataset_variable_ar = cls(
            _uid=variable_uid,
            _sponsor_model_dataset_variable_vo=sponsor_model_dataset_variable_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_dataset_variable_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        sponsor_model_dataset_variable_vo: SponsorModelDatasetVariableVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelDatasetVariableMetadataVO.get_initial_item_metadata(
            author_id=author_id,
            version=sponsor_model_dataset_variable_vo.sponsor_model_version_number,
        )

        sponsor_model_dataset_variable_ar = cls(
            _uid=sponsor_model_dataset_variable_vo.variable_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_dataset_variable_vo=sponsor_model_dataset_variable_vo,
        )
        return sponsor_model_dataset_variable_ar
