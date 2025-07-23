import folium
import geopandas as gpd
from sqlalchemy import create_engine
from shapely.geometry import mapping


if __name__ == "__main__":
    POSTGRES_CONN = "postgresql://postgres:postgres@localhost:5432/mbtagtfs"
    engine = create_engine(POSTGRES_CONN)

    boston = gpd.read_postgis(
        f"SELECT geometry FROM boston_boundary",
        engine,
        geom_col="geometry",
    )

    schools = gpd.read_postgis(
        "SELECT * FROM schools_in_boston",
        engine,
        geom_col="geometry",
    )

    boston = boston.to_crs(epsg=4326)
    schools = schools.to_crs(epsg=4326)

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
            popup=row.get("NAME", "Escuela"),
            tooltip=row.get("NAME", "Escuela"),
            icon=folium.Icon(color="blue", icon="graduation-cap", prefix="fa"),
        ).add_to(m)

    m.save("schools_inside_boston.html")
    print("✅ Mapa generado: schools_inside_boston.html")
