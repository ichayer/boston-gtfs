import geopandas as gpd
import folium as fl
from sqlalchemy import create_engine
import branca.colormap as cm


def get_db_connection():
    db_url = "postgresql://postgres:postgres@localhost:5432/mbtagtfs"
    return create_engine(db_url)


def classify_speed_color(speed):
    if speed <= 20:
        return "#fde0dd"
    elif speed <= 40:
        return "#fa9fb5"
    elif speed <= 80:
        return "#c51b8a"
    elif speed <= 100:
        return "#7a0177"
    else:
        return "#49006a"


if __name__ == "__main__":
    sql = "SELECT * FROM avg_segment_speed_kmh"
    gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geometry", crs="EPSG:4326"
    )

    gdf["color"] = gdf["avg_speed_kmh"].apply(classify_speed_color)

    segment_map = fl.Map(
        location=[42.36, -71.06], tiles="CartoDB positron", zoom_start=12
    )

    for _, row in gdf.iterrows():
        fl.GeoJson(
            row["geometry"].__geo_interface__,
            style_function=lambda feature, color=row["color"]: {
                "color": color,
                "weight": 3,
                "opacity": 0.9,
            },
            tooltip=fl.Tooltip(
                f"Desde: {row['from_stop_name']}<br>"
                f"Hasta: {row['to_stop_name']}<br>"
                f"Velocidad promedio: {row['avg_speed_kmh']:.2f} km/h"
            ),
        ).add_to(segment_map)

    colormap = cm.StepColormap(
        colors=["#fde0dd", "#fcc5c0", "#fa9fb5", "#f768a1", "#c51b8a", "#7a0177"],
        index=[0, 20, 40, 60, 80, 100, 120],
        vmin=0,
        vmax=120,
        caption="Velocidad promedio (km/h)",
    )
    colormap.add_to(segment_map)

    segment_map.save("avg_segment_speed_boston.html")
    print("Mapa guardado como 'avg_segment_speed_boston.html'")
