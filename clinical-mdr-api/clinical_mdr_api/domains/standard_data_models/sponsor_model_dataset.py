import datetime
from dataclasses import dataclass
from typing import Self

from clinical_mdr_api.domains.versioned_object_aggregate import (
    LibraryItemAggregateRootBase,
    LibraryItemMetadataVO,
    LibraryItemStatus,
    LibraryVO,
)


@dataclass(frozen=True)
class SponsorModelDatasetVO:
    """
    The SponsorModelDatasetVO acts as the value object for a single SponsorModelDataset value object
    """

    sponsor_model_name: str
    sponsor_model_version_number: str
    dataset_uid: str
    is_basic_std: bool
    implemented_dataset_class: str | None
    xml_path: str | None
    xml_title: str | None
    structure: str | None
    purpose: str | None
    keys: list[str] | None
    sort_keys: list[str] | None
    is_cdisc_std: bool
    source_ig: str | None
    standard_ref: str | None
    comment: str | None
    ig_comment: str | None
    map_domain_flag: bool
    suppl_qual_flag: bool
    include_in_raw: bool
    gen_raw_seqno_flag: bool
    enrich_build_order: int | None
    label: str | None
    state: str | None
    extended_domain: str | None
    target_data_model_catalogue: str | None = None

    @classmethod
    def from_repository_values(
        cls,
        sponsor_model_name: str,
        sponsor_model_version_number: str,
        dataset_uid: str,
        is_basic_std: bool,
        implemented_dataset_class: str | None,
        xml_path: str | None,
        xml_title: str | None,
        structure: str | None,
        purpose: str | None,
        keys: list[str] | None,
        sort_keys: list[str] | None,
        is_cdisc_std: bool,
        source_ig: str | None,
        standard_ref: str | None,
        comment: str | None,
        ig_comment: str | None,
        map_domain_flag: bool,
        suppl_qual_flag: bool,
        include_in_raw: bool,
        gen_raw_seqno_flag: bool,
        enrich_build_order: int | None,
        label: str | None,
        state: str | None,
        extended_domain: str | None,
        target_data_model_catalogue: str | None = None,
    ) -> Self:
        sponsor_model_dataset_vo = cls(
            sponsor_model_name=sponsor_model_name,
            sponsor_model_version_number=str(sponsor_model_version_number),
            dataset_uid=dataset_uid,
            is_basic_std=is_basic_std,
            implemented_dataset_class=implemented_dataset_class,
            xml_path=xml_path,
            xml_title=xml_title,
            structure=structure,
            purpose=purpose,
            keys=keys,
            sort_keys=sort_keys,
            is_cdisc_std=is_cdisc_std,
            source_ig=source_ig,
            standard_ref=standard_ref,
            comment=comment,
            ig_comment=ig_comment,
            map_domain_flag=map_domain_flag,
            suppl_qual_flag=suppl_qual_flag,
            include_in_raw=include_in_raw,
            gen_raw_seqno_flag=gen_raw_seqno_flag,
            enrich_build_order=enrich_build_order,
            label=label,
            state=state,
            extended_domain=extended_domain,
            target_data_model_catalogue=target_data_model_catalogue,
        )

        return sponsor_model_dataset_vo


class SponsorModelDatasetMetadataVO(LibraryItemMetadataVO):
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
class SponsorModelDatasetAR(LibraryItemAggregateRootBase):
    """
    An abstract generic sponsor model dataset aggregate for versioned sponsor models
    """

    _sponsor_model_dataset_vo: SponsorModelDatasetVO

    @property
    def sponsor_model_dataset_vo(self) -> SponsorModelDatasetVO:
        return self._sponsor_model_dataset_vo

    @sponsor_model_dataset_vo.setter
    def sponsor_model_dataset_vo(self, sponsor_model_dataset_vo: SponsorModelDatasetVO):
        self._sponsor_model_dataset_vo = sponsor_model_dataset_vo

    @property
    def name(self) -> str:
        return self._uid

    @classmethod
    def from_repository_values(
        cls,
        dataset_uid: str,
        sponsor_model_dataset_vo: SponsorModelDatasetVO,
        library: LibraryVO,
        item_metadata: LibraryItemMetadataVO,
    ) -> Self:
        sponsor_model_dataset_ar = cls(
            _uid=dataset_uid,
            _sponsor_model_dataset_vo=sponsor_model_dataset_vo,
            _item_metadata=item_metadata,
            _library=library,
        )
        return sponsor_model_dataset_ar

    @classmethod
    def from_input_values(
        cls,
        *,
        author_id: str,
        sponsor_model_dataset_vo: SponsorModelDatasetVO,
        library: LibraryVO,
    ) -> Self:
        item_metadata = SponsorModelDatasetMetadataVO.get_initial_item_metadata(
            author_id=author_id,
            version=sponsor_model_dataset_vo.sponsor_model_version_number,
        )

        sponsor_model_dataset_ar = cls(
            _uid=sponsor_model_dataset_vo.dataset_uid,
            _item_metadata=item_metadata,
            _library=library,
            _sponsor_model_dataset_vo=sponsor_model_dataset_vo,
        )
        return sponsor_model_dataset_ar
