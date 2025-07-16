from typing import Dict, Union
import pandas as pd
import geopandas as gpd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine


class PostgresClient:
    def __init__(
        self,
        db_user: str,
        db_pass: str,
        db_host: str,
        db_port: str,
        db_name: str,
    ):
        if not all([db_user, db_pass, db_host, db_port, db_name]):
            raise ValueError("All database connection parameters must be provided.")

        self.db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
        self.engine: Engine = create_engine(self.db_url)

    def query(self, sql: str) -> pd.DataFrame:
        with self.engine.connect() as connection:
            return pd.read_sql(sql, connection)

    def query_geodataframe(
        self, sql: str, geom_col: str = "geometry"
    ) -> gpd.GeoDataFrame:
        with self.engine.connect() as connection:
            return gpd.read_postgis(sql, connection, geom_col=geom_col)

    def execute(self, sql: str, params: Union[Dict, None] = None) -> None:
        with self.engine.begin() as connection:
            connection.execute(text(sql), params or {})
