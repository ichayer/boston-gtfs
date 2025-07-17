import geopandas as gpd
import folium as fl
from sqlalchemy import create_engine


def get_db_connection():
    db_url = "postgresql://postgres:postgres@localhost:5432/mbtagtfs"
    return create_engine(db_url)


def generate_color_palette(n):
    basic_colors = [
        "red",
        "blue",
        "green",
        "orange",
        "purple",
        "cyan",
        "magenta",
        "yellow",
        "black",
        "brown",
    ]
    return basic_colors[:n]


if __name__ == "__main__":
    sql = """
    SELECT *
    FROM segment_trip_stats
    WHERE number_of_trips = (SELECT MIN(number_of_trips) FROM segment_trip_stats);
    """
    gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geometry", crs="EPSG:4326"
    )

    # 2. Agrupar por from_stop_id y to_stop_id, y asignar un color por par único
    unique_pairs = (
        gdf[["from_stop_id", "to_stop_id"]].drop_duplicates().reset_index(drop=True)
    )
    unique_pairs["color"] = generate_color_palette(len(unique_pairs))
    gdf = gdf.merge(unique_pairs, on=["from_stop_id", "to_stop_id"])

    segment_map = fl.Map(
        location=[42.3369022, -71.1048019], tiles="CartoDB positron", zoom_start=12
    )

    for _, row in gdf.iterrows():
        fl.GeoJson(
            row["geometry"].__geo_interface__,
            style_function=lambda feature, color=row["color"]: {
                "color": color,
                "weight": 5,
                "opacity": 1.0,
            },
            tooltip=fl.Tooltip(
                f"Desde: {row['from_stop_name']}<br>"
                f"Hasta: {row['to_stop_name']}<br>"
                f"Viajes: {row['number_of_trips']}<br>"
                f"Rutas: {row['routes']}"
            ),
        ).add_to(segment_map)

    segment_map.save("low_segments_colored.html")
    print("Mapa guardado en 'low_segments_colored.html'")
