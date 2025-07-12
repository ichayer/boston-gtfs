import geopandas as gpd
import folium
from sqlalchemy import create_engine


if __name__ == "__main__":
    db_url = "postgresql://postgres:postgres@localhost:5432/mbtagtfs"
    engine = create_engine(db_url)

    query = """
    SELECT trip_id, trajectory
    FROM actual_trips
    WHERE ST_GeometryType(trajectory) = 'ST_LineString'
    """
    gdf = gpd.read_postgis(query, engine, geom_col="trajectory")
    gdf = gdf.to_crs(epsg=4326)

    m = folium.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12
    )

    for _, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row.trajectory.coords]
        folium.PolyLine(
            coords, color="blue", weight=2, opacity=0.6, popup=row.trip_id
        ).add_to(m)

    m.save("raw_tr_boston.html")
