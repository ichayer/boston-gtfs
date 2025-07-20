import folium
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import mapping

# Configurar los íconos y colores para cada tipo de transporte
ROUTE_TYPE_STYLE = {
    0: {"color": "purple", "icon": "train", "label": "Tram / Light rail"},
    1: {"color": "red", "icon": "subway", "label": "Subway / Metro"},
    2: {"color": "darkgreen", "icon": "train", "label": "Train / Rail"},
    3: {"color": "orange", "icon": "bus", "label": "Bus"},
    4: {"color": "cadetblue", "icon": "ship", "label": "Ferry"},
}

if __name__ == "__main__":
    route_type = 4  # 0, 1, 2, 3 o 4

    POSTGRES_CONN = "postgresql://postgres:postgres@localhost:5432/mbtagtfs"
    engine = create_engine(POSTGRES_CONN)

    boston = gpd.read_postgis(
        "SELECT geometry FROM boston_boundary WHERE id = 18",
        engine,
        geom_col="geometry",
    )

    schools = gpd.read_postgis(
        "SELECT * FROM schools_in_boston",
        engine,
        geom_col="geometry",
    )

    stops = gpd.read_postgis(
        f"""
        WITH stops_with_route_types AS (
            SELECT DISTINCT
                s.stop_id,
                s.stop_loc,
                r.route_type
            FROM stops s
            JOIN stop_times st ON s.stop_id = st.stop_id
            JOIN trips t ON st.trip_id = t.trip_id
            JOIN routes r ON t.route_id = r.route_id
        )
        SELECT * FROM stops_with_route_types WHERE route_type = '{route_type}'
        """,
        engine,
        geom_col="stop_loc",
    )

    boston = boston.to_crs(epsg=4326)
    schools = schools.to_crs(epsg=4326)
    stops = stops.to_crs(epsg=4326)

    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=12, tiles="CartoDB positron"
    )

    folium.GeoJson(
        data=mapping(boston.geometry.iloc[0]),
        name="Boston Boundary",
        style_function=lambda x: {
            "fillColor": "#444444",
            "color": "black",
            "weight": 2,
            "fillOpacity": 0.3,
        },
        tooltip="Ciudad de Boston",
    ).add_to(m)

    for _, row in schools.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=row.get("name", "Escuela"),
            tooltip=row.get("name", "Escuela"),
            icon=folium.Icon(color="blue", icon="graduation-cap", prefix="fa"),
        ).add_to(m)

    style = ROUTE_TYPE_STYLE.get(
        route_type, {"color": "gray", "icon": "circle", "label": "Otro"}
    )
    for _, row in stops.iterrows():
        folium.Marker(
            location=[row.stop_loc.y, row.stop_loc.x],
            popup=f"Stop ID: {row['stop_id']}",
            tooltip=style["label"],
            icon=folium.Icon(color=style["color"], icon=style["icon"], prefix="fa"),
        ).add_to(m)

    m.save(f"schools_and_stops_type_{route_type}.html")
    print(f"✅ Mapa generado: schools_and_stops_type_{route_type}.html")
