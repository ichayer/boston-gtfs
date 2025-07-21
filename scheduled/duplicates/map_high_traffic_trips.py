"""
This script generates a single interactive map with transit routes grouped by agency.
Each agency's lines are shown in a distinct color.
"""

import geopandas as gpd
import folium as fl
import colorsys
import random
from sqlalchemy import create_engine


def random_hsv_hex():
    h = random.random()
    s = 0.8
    v = 1
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))


def get_db_connection(
    db_user="postgres",
    db_pass="postgres",
    db_host="localhost",
    db_port="5432",
    db_name="mbtagtfs",
):
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


if __name__ == "__main__":
    sql = """
    WITH trip_id_arrays AS (
        SELECT trip_ids FROM route_count_grid ORDER BY trip_count DESC LIMIT 5
    ),
    relevant_trips AS (
        SELECT * FROM trips WHERE trip_id IN (SELECT unnest(trip_ids) FROM trip_id_arrays)
    )
    SELECT
        trip_id, route_id, service_id, trip_headsign, direction_id,
        ST_SetSRID(shape, 4326) AS geom4326
    FROM relevant_trips t JOIN shapes_aggregated sa ON sa.shape_id = t.shape_id
    """

    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geom4326", crs="EPSG:4326"
    )

    agency_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12
    )

    for service_id, group in shapes_gdf.groupby("service_id"):
        feature_group = fl.FeatureGroup(
            name=f"{service_id}", show=True
        )

        for idx, row in group.iterrows():
            geometry = row["geom4326"]
            popup_text = f"Trip: {row.trip_id}<br>Route: {row.route_id}<br>Service: {row.service_id}<br>Direction: {row.direction_id}"
            if geometry.geom_type == "LineString":
                coords = [(lat, lon) for lon, lat in geometry.coords]
                fl.PolyLine(
                    locations=coords, color=random_hsv_hex(), weight=2, opacity=0.8,
                    popup=fl.Popup(popup_text, max_width=250)
                ).add_to(feature_group)

        feature_group.add_to(agency_map)

    fl.LayerControl(collapsed=False).add_to(agency_map)

    agency_map.save("boston_high_traffic_lines.html")
    print("Map saved to 'boston_high_traffic_lines.html'")
