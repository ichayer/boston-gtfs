import geopandas as gpd
import folium as fl
from sqlalchemy import create_engine
import branca.colormap as cm


def get_db_connection(
    db_user="postgres",
    db_pass="postgres",
    db_host="localhost",
    db_port="5432",
    db_name="mbtagtfs",
):
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


def style_function(feature):
    trips = feature["properties"]["number_of_trips"]
    return {"color": colormap(trips), "weight": 3, "opacity": 0.9}


if __name__ == "__main__":
    sql = "SELECT * FROM segment_trip_stats_june;"

    gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="geometry", crs="EPSG:4326"
    )

    min_val = gdf["number_of_trips"].min()
    max_val = gdf["number_of_trips"].max()
    colormap = cm.LinearColormap(
        colors=[
            "#fff5f0",
            "#fb6a4a",
            "#de2d26",
            "#a50f15",
        ],
        vmin=min_val,
        vmax=max_val,
        caption="Número de viajes por segmento",
    )

    segment_map = fl.Map(
        location=[42.3369022, -71.1048019], tiles="CartoDB positron", zoom_start=12
    )

    fl.GeoJson(
        gdf,
        style_function=style_function,
        tooltip=fl.GeoJsonTooltip(
            fields=["from_stop_name", "to_stop_name", "number_of_trips", "routes"],
            aliases=["Desde", "Hasta", "Numero Total de Viajes", "Rutas"],
            sticky=True,
        ),
    ).add_to(segment_map)

    colormap.add_to(segment_map)

    segment_map.save("segment_trip_stats_june.html")
    print("Mapa guardado en 'segment_trip_stats_june.html'")
