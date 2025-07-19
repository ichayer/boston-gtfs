import os
import folium
import geopandas as gpd
from branca.element import Template, MacroElement
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
    SELECT stop_id, stop_loc, AVG(delay) AS avg_delay
    FROM trip_stops
    GROUP BY stop_id, stop_loc;
    """

    gdf = pg.query_geodataframe(query, geom_col="stop_loc", crs="EPSG:4326")

    # Define color by delay category
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

    # Create map
    m = folium.Map(
        location=[42.3601, -71.0589], zoom_start=13, tiles="CartoDB positron"
    )

    # Add markers
    for _, row in gdf.iterrows():
        lon, lat = row["stop_loc"].x, row["stop_loc"].y
        delay = row["avg_delay"]
        color = get_delay_color(delay)

        popup = (
            f"<b>Stop ID:</b> {row['stop_id']}<br>"
            f"<b>Avg Delay:</b> {round(delay, 2)} min"
        )

        folium.CircleMarker(
            location=(lat, lon),
            radius=1,
            color=color,
            fill=True,
            fill_opacity=0.9,
            popup=folium.Popup(popup, max_width=250),
        ).add_to(m)

    # Custom legend HTML
    legend_html = """
    {% macro html(this, kwargs) %}
    <div style="
        position: fixed;
        bottom: 50px;
        left: 50px;
        width: 180px;
        height: 160px;
        z-index: 1000;
        background-color: white;
        padding: 10px;
        border:2px solid grey;
        font-size:14px;
        ">
        <b>Average Delay (min)</b><br>
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

    # Save
    output_path = "average_delay_per_stop_map.html"
    m.save(output_path)
    print(f"Map saved to: {output_path}")
