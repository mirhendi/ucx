import logging
from dataclasses import dataclass

from databricks.sdk import WorkspaceClient

from databricks.labs.ucx.framework.crawlers import CrawlerBase, SqlBackend

logger = logging.getLogger(__name__)


@dataclass
class Mount:
    name: str
    source: str


class Mounts(CrawlerBase):
    def __init__(self, backend: SqlBackend, ws: WorkspaceClient, inventory_database: str):
        super().__init__(backend, "hive_metastore", inventory_database, "mounts", Mount)
        self._dbutils = ws.dbutils

    def _deduplicate_mounts(self, mounts: list) -> list:
        seen = set()
        deduplicated_mounts = []

        for obj in mounts:
            obj_tuple = (obj.name, obj.source)
            if obj_tuple not in seen:
                seen.add(obj_tuple)
                deduplicated_mounts.append(obj)
        return deduplicated_mounts

    def inventorize_mounts(self):
        self._append_records(self._list_mounts())

    def _list_mounts(self):
        mounts = []
        for mount_point, source, _ in self._dbutils.fs.mounts():
            mounts.append(Mount(mount_point, source))
        return self._deduplicate_mounts(mounts)

    def snapshot(self) -> list[Mount]:
        return self._snapshot(self._try_fetch, self._list_mounts)

    def _try_fetch(self) -> list[Mount]:
        for row in self._fetch(f"SELECT * FROM {self._schema}.{self._table}"):
            yield Mount(*row)
