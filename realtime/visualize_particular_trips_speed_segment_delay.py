import folium
from branca.element import Template, MacroElement
from clients.postgres.postgres_client import PostgresClient


def get_delay_color(delay):
    if delay < 0:
        return "#1a9850"  # strong green
    elif delay <= 5:
        return "#91cf60"  # light green
    elif delay <= 7:
        return "#fee08b"  # yellow
    elif delay <= 10:
        return "#fc8d59"  # orange
    else:
        return "#d73027"  # red


def get_segment_map(pg: PostgresClient, trip_ids: list[str]) -> folium.Map:
    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=13, tiles="CartoDB positron"
    )

    for trip_id in trip_ids:
        query = f"""
        WITH trip_filtered AS (
            SELECT *
            FROM trips_join_segments
            WHERE trip_id = '{trip_id}'
              AND elapsed_time_actual IS NOT NULL
              AND elapsed_time_schedule IS NOT NULL
        )
        SELECT
            geometry,
            start_stop_id,
            end_stop_id,
            elapsed_time_actual,
            elapsed_time_schedule,
            CASE 
                WHEN elapsed_time_actual > elapsed_time_schedule THEN 1
                ELSE 0 
            END AS has_delay
        FROM trip_filtered;
        """

        gdf = pg.query_geodataframe(query, geom_col="geometry", crs="EPSG:4326")
        layer = folium.FeatureGroup(name=f"Trip {trip_id}", show=True)

        for _, row in gdf.iterrows():
            coords = list(row["geometry"].coords)
            color = "red" if row["has_delay"] == 1 else "green"

            tooltip = (
                f"From: {row['start_stop_id']} → {row['end_stop_id']}<br>"
                f"Actual: {round(row['elapsed_time_actual'], 1)} s<br>"
                f"Scheduled: {round(row['elapsed_time_schedule'], 1)} s<br>"
                f"Delay: {'Yes' if row['has_delay'] else 'No'}"
            )

            folium.PolyLine(
                locations=[(lat, lon) for lon, lat in coords],
                color=color,
                weight=4,
                tooltip=tooltip,
            ).add_to(layer)

        layer.add_to(m)

    folium.LayerControl().add_to(m)
    return m


def get_stop_map(pg: PostgresClient, trip_ids: list[str]) -> folium.Map:
    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=13, tiles="CartoDB positron"
    )

    for trip_id in trip_ids:
        query = f"""
        SELECT stop_id, stop_loc, EXTRACT(EPOCH FROM (actual_time - schedule_time)) / 60.0 AS delay
        FROM trip_stops
        WHERE trip_id = '{trip_id}';
        """
        gdf = pg.query_geodataframe(query, geom_col="stop_loc", crs="EPSG:4326")

        layer = folium.FeatureGroup(name=f"Trip {trip_id}", show=True)

        for _, row in gdf.iterrows():
            lon, lat = row["stop_loc"].x, row["stop_loc"].y
            delay = row["delay"]
            color = get_delay_color(delay)

            popup = (
                f"<b>Stop ID:</b> {row['stop_id']}<br>"
                f"<b>Delay:</b> {round(delay, 2)} min"
            )

            folium.CircleMarker(
                location=(lat, lon),
                radius=2,
                color=color,
                fill=True,
                fill_opacity=0.9,
                popup=folium.Popup(popup, max_width=250),
            ).add_to(layer)

        layer.add_to(m)

    _add_legend(m)
    folium.LayerControl().add_to(m)
    return m


def _add_legend(m: folium.Map):
    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="position: fixed; bottom: 50px; left: 50px; width: 180px;
                height: 160px; z-index: 1000; background-color: white;
                padding: 10px; border:2px solid grey; font-size:14px;">
        <b>Stop Delay (min)</b><br>
        <i style="color:#1a9850;">●</i> Early (< 0)<br>
        <i style="color:#91cf60;">●</i> 0–5<br>
        <i style="color:#fee08b;">●</i> 5–7<br>
        <i style="color:#fc8d59;">●</i> 7–10<br>
        <i style="color:#d73027;">●</i> > 10
    </div>
    {% endmacro %}
    """
    legend = MacroElement()
    legend._template = Template(legend_html)
    m.get_root().add_child(legend)


if __name__ == "__main__":
    trip_ids = ["69384386", "68992346"]

    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    stop_map = get_stop_map(pg, trip_ids)
    stop_map.save("trips_stop_delay_map.html")

    segment_map = get_segment_map(pg, trip_ids)
    segment_map.save("trips_segment_delay_map.html")

    print("Maps saved")
