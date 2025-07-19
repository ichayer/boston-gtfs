"""
This script generates a single interactive map with the administrative areas of Massachusetts.
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
    county_colors = {
        'BARNSTABLE': 'darkred',
        'BERKSHIRE': 'purple',
        'BRISTOL': 'orange',
        'DUKES': 'darkgreen',
        'ESSEX': 'cadetblue',
        'FRANKLIN': 'lightgreen',
        'HAMPDEN': 'pink',
        'HAMPSHIRE': 'lightblue',
        'MIDDLESEX': 'green',
        'NANTUCKET': 'gray',
        'NORFOLK': 'cyan',
        'PLYMOUTH': 'lightred',
        'SUFFOLK': 'blue',
        'WORCESTER': 'darkblue',
    }

    sql = """
    SELECT
        gid, town, county,
        St_Transform(geom, 4326) AS geo4326
    FROM townssurvey_poly;
    """

    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geo4326", crs="EPSG:4326"
    )

    town_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=10
    )

    for county_name, group in shapes_gdf.groupby("county"):
        color = county_colors.get(county_name, "red")
        feature_group = fl.FeatureGroup(name=f"{county_name}", show=True)
        for idx, row in group.iterrows():
            geom = row["geo4326"]
            popup_text = f"GID: {row.gid}<br>Town: {row.town}<br>County: {row.county}"
            if geom.geom_type == "Polygon":
                coords = [(lon, lat) for lat, lon in geom.exterior.coords]
                fl.Polygon(
                    locations=coords,
                    color=color,
                    weight=2,
                    opacity=0.6,
                    fill=True,
                    fill_opacity=0.4,
                    popup=fl.Popup(popup_text, max_width=250)
                ).add_to(feature_group)
            elif geom.geom_type == "MultiPolygon":
                for poly in geom.geoms:
                    coords = [(lon, lat) for lat, lon in poly.exterior.coords]
                    fl.Polygon(
                        locations=coords,
                        color=color,
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

    town_map.save("boston_town_polygons_map.html")
    print("Map saved to 'boston_town_polygons_map.html'")
