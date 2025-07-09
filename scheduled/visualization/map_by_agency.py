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

    agency_colors = {
        "1": "blue",  # MBTA
        "3": "orange",  # Cape Cod RTA
    }

    sql = """
    SELECT r.route_id,
        r.route_type,
        sa.shape_id,
        sa.shape,
        a.agency_id,
        a.agency_name
    FROM shapes_aggregated sa
            JOIN trips t ON sa.shape_id = t.shape_id
            JOIN routes r ON t.route_id = r.route_id
            JOIN agency a ON r.agency_id = a.agency_id
    GROUP BY sa.shape_id, sa.shape, a.agency_id, a.agency_name, r.route_type, r.route_id;
    """

    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="shape", crs="EPSG:4326"
    )

    agency_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12
    )

    for agency_id, group in shapes_gdf.groupby("agency_id"):
        color = agency_colors.get(agency_id, "red")
        feature_group = fl.FeatureGroup(
            name=f"{group['agency_name'].iloc[0]} ({color})", show=True
        )

        for geometry in group.geometry:
            if geometry.geom_type == "LineString":
                coords = [(lat, lon) for lon, lat in geometry.coords]
                fl.PolyLine(
                    locations=coords, color=color, weight=2, opacity=0.8
                ).add_to(feature_group)

        feature_group.add_to(agency_map)

    fl.LayerControl(collapsed=False).add_to(agency_map)

    agency_map.save("boston_transit_lines_map_by_agency.html")
    print("Map saved to 'boston_transit_lines_map_by_agency.html'")
