"""
This script generates an interactive map showing a grid over the main areas of Boston.
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
    sql = """
    SELECT
        i, j, trip_count,
        ST_Transform(geom, 4326) AS geo4326
    FROM route_count_grid
    """

    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geo4326", crs="EPSG:4326"
    )

    town_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=10
    )

    feature_group = fl.FeatureGroup(name=f"Heatmap", show=True)

    for _, row in shapes_gdf.iterrows():
        geom = row["geo4326"]
        popup_text = f"Trip count: {row.trip_count}<br>i: {row.i}<br>j: {row.j}"
        if geom.geom_type == "Polygon":
            coords = [(lon, lat) for lat, lon in geom.exterior.coords]
            fl.Polygon(
                locations=coords,
                color="blue",
                weight=2,
                opacity=0.6,
                fill=True,
                fill_opacity=0.4,
                popup=fl.Popup(popup_text, max_width=250)
            ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type: {geom.geom_type} for GID {row.gid}")

    feature_group.add_to(town_map)

    fl.LayerControl(collapsed=False).add_to(town_map)

    town_map.save("boston_grid_empty.html")
    print("Map saved to 'boston_grid_empty.html'")
