# pylint: disable=invalid-name
from neomodel import db

from clinical_mdr_api.domain_repositories.models.feature_flag import (
    FeatureFlag as FeatureFlagNode,
)
from clinical_mdr_api.models.feature_flag import FeatureFlag
from common.exceptions import NotFoundException


class FeatureFlagRepository:
    def _transform_to_model(self, item: FeatureFlagNode) -> FeatureFlag:
        return FeatureFlag(
            sn=item.sn,
            name=item.name,
            enabled=item.enabled,
            description=item.description,
        )

    def _transform_to_models(
        self, data: list[list[FeatureFlagNode]]
    ) -> list[FeatureFlag]:
        return [self._transform_to_model(elm[0]) for elm in data]

    def retrieve_all_feature_flags(self) -> list[FeatureFlag]:
        rs = db.cypher_query(
            """
            MATCH (n:FeatureFlag)
            RETURN n
            """,
            resolve_objects=True,
        )

        return self._transform_to_models(rs[0])

    def find_feature_flag_by_name(self, name: str) -> FeatureFlag | None:
        rs = db.cypher_query(
            """
            MATCH (n:FeatureFlag {name: $name})
            RETURN n
            """,
            params={"name": name},
            resolve_objects=True,
        )

        if rs[0]:
            return self._transform_to_model(rs[0][0][0])

        return None

    def retrieve_feature_flag(self, sn: int) -> FeatureFlag:
        rs = db.cypher_query(
            """
            MATCH (n:FeatureFlag {sn: $sn})
            RETURN n
            """,
            params={"sn": sn},
            resolve_objects=True,
        )

        NotFoundException.raise_if_not(rs[0], "Feature Flag", str(sn), "Serial Number")

        return self._transform_to_model(rs[0][0][0])

    def create_feature_flag(
        self,
        name: str,
        enabled: bool,
        description: str | None,
    ) -> FeatureFlag:
        newest_sn = db.cypher_query(
            """
            MATCH (n:FeatureFlag)
            RETURN n.sn ORDER BY n.sn DESC LIMIT 1
            """,
        )

        sn = int(newest_sn[0][0][0]) + 1 if newest_sn[0] else 1

        rs = db.cypher_query(
            """
            CREATE (n:FeatureFlag)
            SET
                n.sn = $sn,
                n.name = $name,
                n.enabled = $enabled,
                n.description = $description
            RETURN n
            """,
            params={
                "sn": sn,
                "name": name,
                "enabled": enabled,
                "description": description,
            },
            resolve_objects=True,
        )

        return self._transform_to_model(rs[0][0][0])

    def update_feature_flag(self, sn: int, enabled: bool) -> FeatureFlag:
        rs = db.cypher_query(
            """
            MATCH (n:FeatureFlag {sn: $sn})
            SET n.enabled = $enabled
            RETURN n
            """,
            params={"sn": sn, "enabled": enabled},
            resolve_objects=True,
        )

        NotFoundException.raise_if_not(rs[0], "Feature Flag", str(sn), "Serial Number")

        return self._transform_to_model(rs[0][0][0])

    def delete_feature_flag(self, sn: int) -> None:
        db.cypher_query(
            """
            MATCH (n:FeatureFlag {sn: $sn})
            DELETE n
            """,
            params={"sn": sn},
        )
