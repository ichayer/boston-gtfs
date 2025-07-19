import folium
from branca.element import Template, MacroElement
from clients.postgres.postgres_client import PostgresClient


def get_delay_color(delay: float) -> str:
    if delay < 0:
        return "#1a9850"  # strong green (early)
    elif delay <= 5:
        return "#91cf60"  # light green
    elif delay <= 7:
        return "#f9c74f"  # yellow
    elif delay <= 10:
        return "#fc8d59"  # orange
    else:
        return "#d73027"  # red  (heavy delay)


def add_segment_layer(pg: PostgresClient, trip_id: str, fmap: folium.Map):
    """Add a FeatureGroup with all segments for a single trip."""
    query = f"""
        WITH delay_metrics_per_segment AS (
            SELECT
                trip_id,
                start_stop_id,
                end_stop_id,
                geometry,
                elapsed_time_actual,
                elapsed_time_schedule
            FROM trips_join_segments
            WHERE trip_id = '{trip_id}'
        )
        SELECT
            trip_id,
            start_stop_id,
            elapsed_time_actual,
            elapsed_time_schedule,
            end_stop_id,
            geometry,
            CASE WHEN elapsed_time_actual - elapsed_time_schedule > 0 THEN 1 ELSE 0 END AS has_delay
        FROM delay_metrics_per_segment;
    """
    gdf = pg.query_geodataframe(query, geom_col="geometry", crs="EPSG:4326")

    layer = folium.FeatureGroup(
        name=f"Segments – trip {trip_id}", show=False, overlay=True
    )
    for _, row in gdf.iterrows():
        coords = [(lat, lon) for lon, lat in row["geometry"].coords]
        color = "red" if row["has_delay"] else "green"
        tooltip = (
            f"{row['start_stop_id']} → {row['end_stop_id']}<br>"
            f"Delay: {'Yes' if row['has_delay'] else 'No'}<br>"
        )
        folium.PolyLine(coords, color=color, weight=4, tooltip=tooltip).add_to(layer)

    layer.add_to(fmap)


def add_stop_layer(pg: PostgresClient, trip_id: str, fmap: folium.Map):
    """Add a FeatureGroup with all stops for a single trip."""
    query = f"""
        SELECT
            stop_id,
            stop_loc,
            EXTRACT(EPOCH FROM (actual_time - schedule_time))/60.0 AS delay
        FROM trip_stops
        WHERE trip_id = '{trip_id}';
    """
    gdf = pg.query_geodataframe(query, geom_col="stop_loc", crs="EPSG:4326")

    layer = folium.FeatureGroup(
        name=f"Stops – trip {trip_id}", show=False, overlay=True
    )
    for _, row in gdf.iterrows():
        lat, lon = row["stop_loc"].y, row["stop_loc"].x
        delay = row["delay"]
        color = get_delay_color(delay)
        popup = (
            f"<b>Stop ID:</b> {row['stop_id']}<br>"
            f"<b>Delay:</b> {round(delay,2)} min"
        )
        folium.CircleMarker(
            location=(lat, lon),
            radius=5,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=folium.Popup(popup, max_width=250),
        ).add_to(layer)

    layer.add_to(fmap)


def add_legend(fmap: folium.Map):
    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="position: fixed; bottom: 50px; left: 50px; width: 170px;
                background: white; padding: 10px; border:2px solid grey;
                z-index:1000; font-size:14px;">
        <b>Stop Delay (min)</b><br>
        <i style="color:#1a9850;">●</i> Early (&lt; 0)<br>
        <i style="color:#91cf60;">●</i> 0–5<br>
        <i style="color:#fee08b;">●</i> 5–7<br>
        <i style="color:#fc8d59;">●</i> 7–10<br>
        <i style="color:#d73027;">●</i> &gt; 10
    </div>
    {% endmacro %}
    """
    macro = MacroElement()
    macro._template = Template(legend_html)
    fmap.get_root().add_child(macro)


if __name__ == "__main__":
    trip_ids = ["68992342", "68964189"]

    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    # Base map
    fmap = folium.Map(
        location=[42.3601, -71.0589], zoom_start=13, tiles="CartoDB positron"
    )

    # Add layers for every trip
    for trip_id in trip_ids:
        add_segment_layer(pg, trip_id, fmap)
        add_stop_layer(pg, trip_id, fmap)

    add_legend(fmap)
    folium.LayerControl(collapsed=False).add_to(fmap)

    fmap.save("trips_delays_combined.html")
    print("Map saved to trips_delays_combined.html")
