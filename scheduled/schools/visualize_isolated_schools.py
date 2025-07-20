import geopandas as gpd
import folium
import shapely
from sqlalchemy import create_engine
import random

if __name__ == "__main__":

    def random_color():
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))

    engine = create_engine("postgresql://postgres:postgres@localhost:5432/mbtagtfs")

    query = """
    WITH closest_stops AS (
        SELECT DISTINCT ON (s.schid)
        s.schid,
        s.name,
        s.geometry AS school_geom,
        t.stop_id,
        t.stop_loc,
        ST_Distance(s.geometry, ST_Transform(t.stop_loc::geometry, 26986)) AS dist_m
        FROM schools_in_boston s, stops t
        ORDER BY s.schid, ST_Distance(s.geometry, ST_Transform(t.stop_loc::geometry, 26986))),

    top5 AS (SELECT * FROM closest_stops ORDER BY dist_m DESC LIMIT 5)
    SELECT * FROM top5;
    """

    gdf = gpd.read_postgis(query, engine, geom_col="school_geom")
    gdf.set_geometry("school_geom", inplace=True)
    gdf = gdf.to_crs(epsg=4326)

    if isinstance(gdf["stop_loc"].iloc[0], str):
        gdf["stop_geom"] = gdf["stop_loc"].apply(shapely.wkb.loads)
    else:
        gdf["stop_geom"] = gdf["stop_loc"]

    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=12, tiles="CartoDB positron"
    )

    for _, row in gdf.iterrows():
        color = random_color()

        folium.Marker(
            location=[row.school_geom.y, row.school_geom.x],
            popup=f"{row.name} ({round(row.dist_m)} m)",
            tooltip="Colegio",
            icon=folium.Icon(color="red", icon="graduation-cap", prefix="fa"),
        ).add_to(m)

        folium.CircleMarker(
            location=[row.stop_geom.y, row.stop_geom.x],
            radius=6,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.8,
            tooltip=f"Parada {row.stop_id}",
        ).add_to(m)

        folium.PolyLine(
            locations=[
                [row.school_geom.y, row.school_geom.x],
                [row.stop_geom.y, row.stop_geom.x],
            ],
            color=color,
            weight=2,
            opacity=0.6,
        ).add_to(m)

    m.save("top5_schools_most_isolated.html")
    print("✅ Mapa generado: top5_schools_most_isolated.html")
