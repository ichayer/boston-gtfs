import pandas as pd
from clients.postgres.postgres_client import PostgresClient


if __name__ == "__main__":
    postgres_client = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )
    df = pd.read_csv("vehicle_positions.csv")
    df.to_sql(
        "vehicle_positions", postgres_client.engine, if_exists="replace", index=False
    )
