"""
This script connects to a PostGIS-enabled PostgreSQL database containing transit line shapes
and generates an interactive map to visualize individual transit routes using Folium and GeoPandas.
Each route is shown as a separate layer that can be toggled on/off.
"""

import folium as fl
import geopandas as gpd
from sqlalchemy import create_engine


sql = "SELECT * FROM shapes_aggregated;"


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
    shapes_gdf = gpd.read_postgis(
        sql,
        get_db_connection(),
        geom_col="shape",
        crs="EPSG:4326",
    )

    map_indiv_lines = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12
    )

    for shape_id, shape_group in shapes_gdf.groupby("shape_id"):
        feature_group = fl.FeatureGroup(name=f"Route {shape_id}", show=True)

        for geometry in shape_group.geometry:
            if geometry.geom_type == "LineString":

                coords = [(lat, lon) for lon, lat in geometry.coords]
                fl.PolyLine(
                    locations=coords, color="blue", weight=2, opacity=0.1
                ).add_to(feature_group)

        feature_group.add_to(map_indiv_lines)

    fl.LayerControl(collapsed=False).add_to(map_indiv_lines)

    map_indiv_lines.save("boston_transit_lines_map.html")
    print("Map saved to boston_transit_lines_map.html")
