import folium
from branca.colormap import LinearColormap
from clients.postgres.postgres_client import PostgresClient

if __name__ == "__main__":
    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    query = """
        SELECT
            real_avg_speed,
            scheduled_avg_speed,
            (real_avg_speed - scheduled_avg_speed) AS speed_diff,
            geometry,
            from_stop_name,
            to_stop_name
        FROM avg_speed_diff_per_segment
    """
    gdf = pg.query_geodataframe(query, geom_col="geometry", crs="EPSG:4326")

    center = [42.3601, -71.0589]
    zoom = 12

    # -------- Map 1: Scheduled Speed --------
    m_sched = folium.Map(location=center, tiles="CartoDB positron", zoom_start=zoom)
    colormap_sched = LinearColormap(
        colors=["white", "yellow", "orange", "red", "darkred"],
        vmin=0,
        vmax=60,
        caption="Scheduled Speed (km/h)",
    )
    colormap_sched.add_to(m_sched)

    for _, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row.geometry.coords]
        color = colormap_sched(row.scheduled_avg_speed)
        folium.PolyLine(
            coords,
            color=color,
            weight=3,
            opacity=0.7,
            tooltip=f"{row.from_stop_name} → {row.to_stop_name}<br>Scheduled: {row.scheduled_avg_speed:.1f} km/h",
        ).add_to(m_sched)

    m_sched.save("map_scheduled_speed.html")

    # -------- Map 2: Real Speed --------
    m_real = folium.Map(location=center, tiles="CartoDB positron", zoom_start=zoom)
    colormap_real = LinearColormap(
        colors=["white", "yellow", "orange", "red", "darkred"],
        vmin=0,
        vmax=60,
        caption="Real Speed (km/h)",
    )
    colormap_real.add_to(m_real)

    for _, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row.geometry.coords]
        color = colormap_real(row.real_avg_speed)
        folium.PolyLine(
            coords,
            color=color,
            weight=3,
            opacity=0.7,
            tooltip=f"{row.from_stop_name} → {row.to_stop_name}<br>Real: {row.real_avg_speed:.1f} km/h",
        ).add_to(m_real)

    m_real.save("map_real_speed.html")

    # -------- Map 3: Speed Difference --------
    m_diff = folium.Map(location=center, tiles="CartoDB positron", zoom_start=zoom)
    colormap_diff = LinearColormap(
        colors=["darkblue", "blue", "white", "orange", "red"],
        vmin=-20,
        vmax=20,
        caption="Speed Difference (Real - Scheduled)",
    )
    colormap_diff.add_to(m_diff)

    for _, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row.geometry.coords]
        color = colormap_diff(row.speed_diff)
        folium.PolyLine(
            coords,
            color=color,
            weight=3,
            opacity=0.7,
            tooltip=f"{row.from_stop_name} → {row.to_stop_name}<br>Diff: {row.speed_diff:.1f} km/h",
        ).add_to(m_diff)

    m_diff.save("map_speed_diff.html")
