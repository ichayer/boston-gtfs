import geopandas as gpd
import folium as fl
from sqlalchemy import create_engine
import itertools


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
    SELECT *
    FROM segments
    WHERE route_id = '8'
    AND direction_id = 1
    AND shape_id = '080277'
    ORDER BY stop_sequence;
    """

    gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geometry", crs="EPSG:4326"
    )

    # Harvard University
    segment_map = fl.Map(
        location=[42.3369022, -71.1048019], tiles="CartoDB positron", zoom_start=16
    )

    colors = itertools.cycle(
        [
            "red",
            "blue",
            "green",
            "purple",
            "orange",
            "darkred",
            "cadetblue",
            "darkgreen",
            "pink",
            "lightgray",
            "black",
            "darkblue",
            "gold",
        ]
    )

    for _, row in gdf.iterrows():
        if row.geometry.geom_type == "LineString":
            coords = [(lat, lon) for lon, lat in row.geometry.coords]
            fl.PolyLine(
                locations=coords,
                color=next(colors),
                weight=5,
                opacity=0.9,
                tooltip=fl.Tooltip(row.segment_name, sticky=True),
            ).add_to(segment_map)

    fl.Marker(
        location=[42.336984, -71.103274],
        popup="Harvard University",
        tooltip="Harvard University",
        icon=fl.Icon(color="blue", icon="university", prefix="fa"),
    ).add_to(segment_map)

    fl.Marker(
        location=[42.3388099, -71.1006666],
        popup="Simmons University",
        tooltip="Simmons University",
        icon=fl.Icon(color="red", icon="university", prefix="fa"),
    ).add_to(segment_map)

    fl.Marker(
        location=[42.340803, -71.1030563],
        popup="Emmanuel College",
        tooltip="Emmanuel College",
        icon=fl.Icon(color="red", icon="university", prefix="fa"),
    ).add_to(segment_map)

    fl.Marker(
        location=[42.336409, -71.072444],
        popup="Boston University School of Medicine",
        tooltip="Boston University School of Medicine",
        icon=fl.Icon(color="red", icon="university", prefix="fa"),
    ).add_to(segment_map)

    fl.Marker(
        location=[42.3162986, -71.0390149],
        popup="Edward M. Kennedy Institute for the United States Senate",
        tooltip="Edward M. Kennedy Institute for the United States Senate",
        icon=fl.Icon(color="red", icon="university", prefix="fa"),
    ).add_to(segment_map)

    segment_map.save("route_8_shape_080277_colored_segments.html")
    print(
        "Ruta 8 visualizada con colores por segmento en 'route_8_shape_080277_colored_segments.html'"
    )
