from gtfs_functions import Feed
from sqlalchemy import create_engine

if __name__ == "__main__":
    # 1. Path to the GTFS zip file
    gtfs_file = "data.zip"

    # 2. Date range for filtering trips and services
    start_date = "2025-01-01"
    end_date = "2025-12-31"

    # 3. Load GTFS feed and extract route segments between consecutive stops
    feed = Feed(gtfs_file, start_date=start_date, end_date=end_date)
    segments = feed.segments  # Returns a GeoDataFrame with line segments

    # 4. PostgreSQL/PostGIS connection parameters
    db_user = "postgres"
    db_pass = "postgres"
    db_host = "localhost"
    db_port = "5432"
    db_name = "mbtagtfs"
    table_name = "segments"

    # 5. Create SQLAlchemy connection URL
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)

    # 6. Save segments to the PostGIS database (overwrites table if it exists)
    segments.to_postgis(table_name, engine, if_exists="replace")
    print(f"Table '{table_name}' successfully saved to database '{db_name}'.")
