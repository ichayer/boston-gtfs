from folium import Map, PolyLine, FeatureGroup, LayerControl
from clients.postgres.postgres_client import PostgresClient
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

if __name__ == "__main__":
    postgres_client = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    m = Map(location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12)

    query = "SELECT * FROM map_matched_bus_trips ORDER BY trip_id;"
    gdf = postgres_client.query_geodataframe(query, geom_col="geom")
    gdf = gdf.to_crs(epsg=4326)

    # Big color pallet
    cmap = plt.get_cmap("nipy_spectral", len(gdf))
    trip_id_to_color = {
        trip_id: mcolors.rgb2hex(cmap(i)[:3])
        for i, trip_id in enumerate(sorted(gdf.trip_id.unique()))
    }

    for i, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row.geom.coords]
        color = trip_id_to_color[row.trip_id]
        group = FeatureGroup(name=f"Trip {row.trip_id}", show=True)
        PolyLine(coords, color=color, weight=2, opacity=0.7, popup=row.trip_id).add_to(
            group
        )
        group.add_to(m)

    LayerControl(collapsed=False).add_to(m)
    m.save("bus_interpolated_geometries.html")
