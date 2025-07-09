"""
This script generates a single interactive map with transit routes grouped by agency.
Each agency's lines are shown in a distinct color.
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

    route_type_colors = {
        "0": "green",  # Tram / Light rail
        "1": "black",  # Subway / Metro
        "2": "blue",  # Rail (long-distance)
        "3": "orange",  # Bus
        "4": "red",  # ferry
    }

    sql = """
    SELECT r.route_id,
        r.route_type,
        CASE r.route_type
            WHEN '0' THEN 'Tram / Light rail'
            WHEN '1' THEN 'Subway / Metro'
            WHEN '2' THEN 'Rail (long-distance)'
            WHEN '3' THEN 'Bus'
            WHEN '4' THEN 'Ferry'
            WHEN '5' THEN 'Cable tram'
            WHEN '6' THEN 'Aerial lift'
            WHEN '7' THEN 'Funicular'
            WHEN '11' THEN 'Trolleybus'
            WHEN '12' THEN 'Monorail'
            ELSE 'Other / Unknown'
            END AS route_type_name,
        sa.shape_id,
        sa.shape
    FROM shapes_aggregated sa
            JOIN trips t ON sa.shape_id = t.shape_id
            JOIN routes r ON t.route_id = r.route_id
    GROUP BY sa.shape_id, sa.shape, r.route_type, r.route_id;
    """

    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="shape", crs="EPSG:4326"
    )

    route_type_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12
    )

    for route_type, group in shapes_gdf.groupby("route_type"):
        color = route_type_colors.get(route_type, "purple")
        feature_group = fl.FeatureGroup(
            name=f"{group['route_type_name'].iloc[0]} ({color})", show=True
        )

        for geometry in group.geometry:
            if geometry.geom_type == "LineString":
                coords = [(lat, lon) for lon, lat in geometry.coords]
                fl.PolyLine(
                    locations=coords, color=color, weight=2, opacity=0.8
                ).add_to(feature_group)

        feature_group.add_to(route_type_map)

    fl.LayerControl(collapsed=False).add_to(route_type_map)

    route_type_map.save("boston_transit_lines_map_by_route_type.html")
    print("Map saved to 'boston_transit_lines_map_by_route_type.html'")
