import folium
from realtime.clients.postgres.postgres_client import PostgresClient

if __name__ == "__main__":

    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    # Select trip
    # 6, 28, 31
    trip_index = 31
    trip_id_sql = f"""

    SELECT trip_id
    FROM map_matched_bus_trips
    ORDER BY trip_id
    OFFSET {trip_index} LIMIT 1;
    """
    trip_id = pg.query(trip_id_sql).iloc[0]["trip_id"]
    print(f"Visualizando trip_id: {trip_id}")

    # 1. Real trajectory
    trajectory_sql = f"""
    SELECT geom AS geometry
    FROM map_matched_bus_trips
    WHERE trip_id = '{trip_id}';
    """
    trajectory_gdf = pg.query_geodataframe(
        trajectory_sql, geom_col="geometry", crs="EPSG:4326"
    )
    trajectory_geom = trajectory_gdf.geometry.iloc[0]

    # 2. Scheduled stops (stop_loc + nombre real)
    scheduled_sql = f"""
    SELECT s.stop_loc AS geometry, s.stop_name
    FROM arrivals_departures ad
    JOIN stops s ON ad.stop_id = s.stop_id
    WHERE ad.trip_id = '{trip_id}';
    """
    scheduled_stops = pg.query_geodataframe(
        scheduled_sql, geom_col="geometry", crs="EPSG:4326"
    )

    # 3. Detected stops (stop_loc + stop_id)
    realtime_sql = f"""
    SELECT stop_loc AS geometry, stop_id
    FROM trip_stops
    WHERE trip_id = '{trip_id}';
    """
    realtime_stops = pg.query_geodataframe(
        realtime_sql, geom_col="geometry", crs="EPSG:4326"
    )

    # Crear el mapa centrado en el primer punto de la trayectoria
    start_coords = [trajectory_geom.coords[0][1], trajectory_geom.coords[0][0]]
    m = folium.Map(location=start_coords, zoom_start=14)

    # Línea azul: trayectoria real
    folium.PolyLine(
        locations=[(y, x) for x, y in trajectory_geom.coords],
        color="blue",
        weight=4,
        tooltip="Trayectoria real",
    ).add_to(m)

    # Paradas programadas (con stop_name)
    for _, row in scheduled_stops.iterrows():
        folium.CircleMarker(
            location=[row.geometry.y, row.geometry.x],
            radius=6,
            color="red",
            fill=True,
            fill_opacity=0.9,
            tooltip=f"Parada programada: {row.stop_name}",
        ).add_to(m)

    # Paradas detectadas (con stop_id)
    for _, row in realtime_stops.iterrows():
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            icon=folium.Icon(color="green", icon="ok-sign"),
            tooltip=f"Parada detectada: {row.stop_id}",
        ).add_to(m)

    # Guardar HTML
    output_path = f"trip.html"
    m.save(output_path)
    print(f"Mapa guardado en {output_path}")
