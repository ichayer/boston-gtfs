import folium
from clients.postgres.postgres_client import PostgresClient

TRIP_ID = "68992342"

if __name__ == "__main__":
    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=13, tiles="CartoDB positron"
    )

    # Layer 1: Map-matched trajectory
    traj_query = f"""
        SELECT trip_id, geom AS geometry
        FROM map_matched_bus_trips
        WHERE trip_id = '{TRIP_ID}';
    """
    traj_gdf = pg.query_geodataframe(traj_query, geom_col="geometry", crs="EPSG:4326")

    traj_layer = folium.FeatureGroup(name="Matched Trajectory", show=True)
    for _, row in traj_gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row["geometry"].coords]
        folium.PolyLine(
            coords, color="blue", weight=4, tooltip=f"Trip: {row['trip_id']}"
        ).add_to(traj_layer)
    traj_layer.add_to(m)

    # Layer 2: Segments
    seg_query = f"""
        SELECT start_stop_id, end_stop_id, geometry
        FROM trips_join_segments
        WHERE trip_id = '{TRIP_ID}';
    """
    seg_gdf = pg.query_geodataframe(seg_query, geom_col="geometry", crs="EPSG:4326")

    seg_layer = folium.FeatureGroup(name="Trip Segments", show=False)
    for _, row in seg_gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row["geometry"].coords]
        tooltip = f"{row['start_stop_id']} → {row['end_stop_id']}"
        folium.PolyLine(coords, color="orange", weight=4, tooltip=tooltip).add_to(
            seg_layer
        )
    seg_layer.add_to(m)

    # Layer 3: Trip stops
    stop_query = f"""
        SELECT stop_id, stop_loc, EXTRACT(EPOCH FROM (actual_time - schedule_time)) / 60.0 AS delay
        FROM trip_stops
        WHERE trip_id = '{TRIP_ID}';
    """
    stop_gdf = pg.query_geodataframe(stop_query, geom_col="stop_loc", crs="EPSG:4326")

    stop_layer = folium.FeatureGroup(name="Trip Stops", show=False)
    for _, row in stop_gdf.iterrows():
        lat, lon = row["stop_loc"].y, row["stop_loc"].x
        delay = round(row["delay"], 1) if row["delay"] is not None else "N/A"
        tooltip = f"Stop: {row['stop_id']}<br>Delay: {delay} min"
        folium.CircleMarker(
            location=(lat, lon),
            radius=5,
            color="black",
            fill=True,
            fill_color="red" if delay != "N/A" and delay > 5 else "green",
            fill_opacity=0.8,
            tooltip=tooltip,
        ).add_to(stop_layer)
    stop_layer.add_to(m)

    folium.LayerControl().add_to(m)

    m.save("trip_components.html")
    print("Map saved to trip_components.html")
