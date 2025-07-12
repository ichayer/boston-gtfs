import pandas as pd
from sqlalchemy import create_engine


if __name__ == "__main__":
    engine = create_engine("postgresql://postgres:postgres@localhost:5432/mbtagtfs")
    df = pd.read_csv("vehicle_positions.csv")
    df.to_sql("vehicle_positions", engine, if_exists="replace", index=False)
