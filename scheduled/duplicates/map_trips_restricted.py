"""
This script generates a single interactive map with the trips restricted to the date and
time range we're analyzing for duplicates, taken from the trips_active_restricted table.
"""

import geopandas as gpd
import folium as fl
from sqlalchemy import create_engine


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
    nice_color_index = 0
    nice_colors = [
        "red", "orange", "yellow", "green", "blue", "purple", "pink", "cadetblue",
        "lightgreen", "lightblue", "beige", "gray", "darkred", "darkblue", "darkgreen", "cyan",
        "lightgray", "lightyellow", "lightpink", "lightpurple", "lightorange", "lightcyan",
        "teal", "magenta", "gold", "lime", "navy", "maroon", "olive", "aqua", "coral",
        "salmon", "indigo", "violet", "turquoise", "mint", "brown", "tan", "peach", "plum", "black"
    ]

    sql = """
    SELECT
        *,
        St_Transform(geom_restricted, 4326) AS geo4326
    FROM trips_active_restricted;
    """

    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geo4326", crs="EPSG:4326"
    )

    town_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=10
    )

    for service_id, group in shapes_gdf.groupby("service_id"):
        color = nice_colors[nice_color_index]
        if (nice_color_index < len(nice_colors) - 1):
            nice_color_index += 1

        feature_group = fl.FeatureGroup(name=f"{service_id}", show=True)
        for idx, row in group.iterrows():
            geom = row["geo4326"]
            popup_text = f"Service: {row.service_id}<br>Trip: {row.trip_id}<br>Route: {row.route_id}"
            if geom.geom_type == "LineString":
                coords = [(lat, lon) for lon, lat in geom.coords]
                fl.PolyLine(
                    locations=coords, color=color, weight=2, opacity=0.1
                ).add_to(feature_group)
            elif geom.geom_type == "MultiLineString":
                for line in geom.geoms:
                    coords = [(lat, lon) for lon, lat in line.coords]
                    fl.PolyLine(
                        locations=coords, color=color, weight=2, opacity=0.1
                    ).add_to(feature_group)
            else:
                print(f"Unsupported geometry type: {geom.geom_type} for service {row.service_id} trip {row.trip_id} route {row.route_id}")

        feature_group.add_to(town_map)

    fl.LayerControl(collapsed=False).add_to(town_map)

    town_map.save("bostom_trips_restricted.html")
    print("Map saved to 'bostom_trips_restricted.html'")
