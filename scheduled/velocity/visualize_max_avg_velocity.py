import geopandas as gpd
import folium as fl
from sqlalchemy import create_engine


def get_db_connection():
    db_url = "postgresql://postgres:postgres@localhost:5432/mbtagtfs"
    return create_engine(db_url)


if __name__ == "__main__":
    sql = """
    SELECT *
    FROM avg_segment_speed_kmh_june_july
    WHERE avg_speed_kmh = (SELECT MAX(avg_speed_kmh) FROM avg_segment_speed_kmh_june_july);
    """
    gdf = gpd.read_postgis(sql, get_db_connection(), geom_col="geometry", crs="EPSG:4326")

    min_speed = gdf["avg_speed_kmh"].min()
    gdf["color"] = gdf["avg_speed_kmh"].apply(lambda v: "blue" if v == min_speed else "red")

    segment_map = fl.Map(location=[42.36, -71.06], tiles="CartoDB positron", zoom_start=13)

    for _, row in gdf.iterrows():
        fl.GeoJson(
            row["geometry"].__geo_interface__,
            style_function=lambda feature, color=row["color"]: {
                "color": color,
                "weight": 5,
                "opacity": 0.9,
            },
            tooltip=fl.Tooltip(
                f"<b>Desde:</b> {row['from_stop_name']}<br>"
                f"<b>Hasta:</b> {row['to_stop_name']}<br>"
                f"<b>Velocidad promedio:</b> {row['avg_speed_kmh']:.2f} km/h"
            ),
        ).add_to(segment_map)

    segment_map.save("max_segment_speeds.html")
    print("Mapa guardado como 'max_segment_speeds.html'")
