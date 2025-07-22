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

    query = """
    WITH delay_metrics_per_segment AS (
        SELECT
            start_stop_id,
            end_stop_id,
            geometry,
            COUNT(*) AS no_trips_seg,
            AVG(elapsed_time_actual) AS avg_actual,
            AVG(elapsed_time_schedule) AS avg_schedule
        FROM trips_join_segments
        GROUP BY start_stop_id, end_stop_id, geometry
    )
    SELECT
        geometry,
        no_trips_seg,
        CASE WHEN avg_actual - avg_schedule > 0 THEN 1 ELSE 0 END as has_delay
    FROM delay_metrics_per_segment;
    """

    gdf = pg.query_geodataframe(query, geom_col="geometry", crs="EPSG:4326")

    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=13, tiles="CartoDB positron"
    )

    for _, row in gdf.iterrows():
        coords = list(row["geometry"].coords)
        color = "red" if row["has_delay"] == 1 else "green"
        tooltip = f"Trips: {row['no_trips_seg']}, Delay: {'Yes' if row['has_delay'] else 'No'}"

        folium.PolyLine(
            locations=[(lat, lon) for lon, lat in coords],
            color=color,
            weight=4,
            tooltip=tooltip,
        ).add_to(m)

    output_path = "segment_delay_binary_map.html"
    m.save(output_path)
    print(f"Map saved to: {output_path}")
