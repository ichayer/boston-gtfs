"""
This script generates an interactive map showing possible duplicate routes in Boston.
"""

import geopandas as gpd
import folium as fl
import colorsys
import random
from sqlalchemy import create_engine
import shapely.wkb


def random_hsv_hex():
    h = random.random()
    s = 0.8
    v = 1
    r, g, b = colorsys.hsv_to_rgb(h, s, v)
    return '#{:02x}{:02x}{:02x}'.format(int(r*255), int(g*255), int(b*255))


def get_db_connection(
    db_user="postgres",
    db_pass="postgres",
    db_host="localhost",
    db_port="25432",
    db_name="mbtagtfs",
):
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    return create_engine(db_url)


if __name__ == "__main__":
    sql = """
WITH trip_pairs AS (
    SELECT
        t1.trip_id AS trip1_id,
        t2.trip_id AS trip2_id,
        t1.shape_id AS trip1_shape_id,
        t2.shape_id AS trip2_shape_id,
        t1.service_id AS trip1_service_id,
        t2.service_id AS trip2_service_id,
        t1.route_id AS trip1_route_id,
        t2.route_id AS trip2_route_id,
        t1.trip_headsign AS trip1_headsign,
        t2.trip_headsign AS trip2_headsign,
        t1.direction_id AS trip1_direction,
        t2.direction_id AS trip2_direction,
        ST_Transform(t1.stops_geom, 4326) AS trip1_stops_geom,
        ST_Transform(t2.stops_geom, 4326) AS trip2_stops_geom,
        ST_Transform(t1.stops_geom_buffer, 4326) AS trip1_stops_geom_buffer,
        ST_Transform(t2.stops_geom_buffer, 4326) AS trip2_stops_geom_buffer,
        t1.stops_geom_buffer_area AS trip1_stops_geom_buffer_area,
        t2.stops_geom_buffer_area AS trip2_stops_geom_buffer_area,
        ST_Transform(ST_Intersection(t1.stops_geom_buffer, t2.stops_geom_buffer), 4326) AS buffer_intersection,
        ST_Area(ST_Intersection(t1.stops_geom_buffer, t2.stops_geom_buffer)) AS buffer_intersection_area,
        ST_SetSRID(sa1.shape, 4326) AS trip1_shape,
        ST_SetSRID(sa2.shape, 4326) AS trip2_shape
    FROM high_traffic_trips_with_stops_geom t1 JOIN high_traffic_trips_with_stops_geom t2
        ON t1.trip_id < t2.trip_id AND ST_Intersects(t1.stops_geom_buffer, t2.stops_geom_buffer)
        AND t1.service_id != t2.service_id AND t1.route_id != t2.route_id AND t1.direction_id = t2.direction_id
        JOIN shapes_aggregated sa1 ON sa1.shape_id = t1.shape_id
        JOIN shapes_aggregated sa2 ON sa2.shape_id = t2.shape_id
)
SELECT DISTINCT ON (tp.trip1_service_id, tp.trip1_route_id, tp.trip2_service_id, tp.trip2_route_id)
    (tp.buffer_intersection_area * 100 / LEAST(tp.trip1_stops_geom_buffer_area, tp.trip2_stops_geom_buffer_area)) AS intersection_percentage,
    tp.*
FROM trip_pairs tp
WHERE (tp.buffer_intersection_area * 100 / LEAST(tp.trip1_stops_geom_buffer_area, tp.trip2_stops_geom_buffer_area)) > 60
    """

    print("Running query...")
    shapes_gdf = gpd.read_postgis(
        sql, get_db_connection(), geom_col="buffer_intersection", crs="EPSG:4326"
    )

    print(f"Got {len(shapes_gdf)} rows")
    # Manually convert geometry columns from WKB hex to shapely objects
    for col in [
        "trip1_stops_geom", "trip2_stops_geom",
        "trip1_stops_geom_buffer", "trip2_stops_geom_buffer",
        "trip1_shape", "trip2_shape",
        "buffer_intersection"
    ]:
        shapes_gdf[col] = shapes_gdf[col].apply(
            lambda x: shapely.wkb.loads(x, hex=True) if isinstance(x, str) else x
        )

    print("Creating map...")
    duplicates_map = fl.Map(
        location=[42.3601, -71.0589], tiles="CartoDB positron", zoom_start=12
    )

    is_first = True
    for idx, row in shapes_gdf.iterrows():
        feature_group = fl.FeatureGroup(
            name=f"{row.trip1_id}-{row.trip2_id} {row.intersection_percentage:.1f}%", show=is_first
        )
        is_first = False

        print(f"Processing pair {row.trip1_id}-{row.trip2_id} {row.intersection_percentage:.1f}%")

        # Trip 1 popup
        popup1 = lambda: fl.Popup(
            f"Trip ID: {row.trip1_id}<br>"
            f"Shape ID: {row.trip1_shape_id}<br>"
            f"Service ID: {row.trip1_service_id}<br>"
            f"Route ID: {row.trip1_route_id}<br>"
            f"HeadSign: {row.trip1_headsign}<br>"
            f"Direction: {row.trip1_direction}",
            max_width=250
        )

        # Trip 2 popup
        popup2 = lambda: fl.Popup(
            f"Trip ID: {row.trip2_id}<br>"
            f"Shape ID: {row.trip2_shape_id}<br>"
            f"Service ID: {row.trip2_service_id}<br>"
            f"Route ID: {row.trip2_route_id}<br>"
            f"HeadSign: {row.trip2_headsign}<br>"
            f"Direction: {row.trip2_direction}",
            max_width=250
        )

        # Polygon/MultiPolygon: trip1_stops_geom_buffer
        geom1_buffer = row["trip1_stops_geom_buffer"]
        if geom1_buffer.geom_type == "Polygon":
            fl.Polygon(
                locations=[(lat, lon) for lon, lat in geom1_buffer.exterior.coords],
                color="red", fill=True, fill_color="red", fill_opacity=0.2, weight=1,
                popup=popup1()
            ).add_to(feature_group)
        elif geom1_buffer.geom_type == "MultiPolygon":
            for poly in geom1_buffer.geoms:
                fl.Polygon(
                    locations=[(lat, lon) for lon, lat in poly.exterior.coords],
                    color="red", fill=True, fill_color="red", fill_opacity=0.2, weight=1,
                    popup=popup1()
                ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type for trip1_stops_geom_buffer: {geom1_buffer.geom_type}")

        # Polygon/MultiPolygon: trip2_stops_geom_buffer
        geom2_buffer = row["trip2_stops_geom_buffer"]
        if geom2_buffer.geom_type == "Polygon":
            fl.Polygon(
                locations=[(lat, lon) for lon, lat in geom2_buffer.exterior.coords],
                color="blue", fill=True, fill_color="blue", fill_opacity=0.2, weight=1,
                popup=popup2()
            ).add_to(feature_group)
        elif geom2_buffer.geom_type == "MultiPolygon":
            for poly in geom2_buffer.geoms:
                fl.Polygon(
                    locations=[(lat, lon) for lon, lat in poly.exterior.coords],
                    color="blue", fill=True, fill_color="blue", fill_opacity=0.2, weight=1,
                    popup=popup2()
                ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type for trip2_stops_geom_buffer: {geom2_buffer.geom_type}")

        # LineString/MultiLineString: trip1_shape
        shape1 = row["trip1_shape"]
        if shape1.geom_type == "LineString":
            coords = [(lat, lon) for lon, lat in shape1.coords]
            fl.PolyLine(
                locations=coords, color="red", weight=3, opacity=1.0,
                popup=popup1()
            ).add_to(feature_group)
        elif shape1.geom_type == "MultiLineString":
            for line in shape1.geoms:
                coords = [(lat, lon) for lon, lat in line.coords]
                fl.PolyLine(
                    locations=coords, color="red", weight=3, opacity=1.0,
                    popup=popup1()
                ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type for trip1_shape: {shape1.geom_type}")

        # LineString/MultiLineString: trip2_shape
        shape2 = row["trip2_shape"]
        if shape2.geom_type == "LineString":
            coords = [(lat, lon) for lon, lat in shape2.coords]
            fl.PolyLine(
                locations=coords, color="blue", weight=3, opacity=1.0,
                popup=popup2()
            ).add_to(feature_group)
        elif shape2.geom_type == "MultiLineString":
            for line in shape2.geoms:
                coords = [(lat, lon) for lon, lat in line.coords]
                fl.PolyLine(
                    locations=coords, color="blue", weight=3, opacity=1.0,
                    popup=popup2()
                ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type for trip2_shape: {shape2.geom_type}")

        # MultiPoint: trip1_stops_geom
        if row["trip1_stops_geom"].geom_type == "MultiPoint":
            for pt in row["trip1_stops_geom"].geoms:
                fl.CircleMarker(
                    location=[pt.y, pt.x], radius=4, color="red", fill=True, fill_color="red",
                    popup=popup1()
                ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type for trip1_stops_geom: {row['trip1_stops_geom'].geom_type}")

        # MultiPoint: trip2_stops_geom
        if row["trip2_stops_geom"].geom_type == "MultiPoint":
            for pt in row["trip2_stops_geom"].geoms:
                fl.CircleMarker(
                    location=[pt.y, pt.x], radius=4, color="blue", fill=True, fill_color="blue",
                    popup=popup2()
                ).add_to(feature_group)
        else:
            print(f"Unsupported geometry type for trip2_stops_geom: {row['trip2_stops_geom'].geom_type}")

        feature_group.add_to(duplicates_map)

    fl.LayerControl(collapsed=False).add_to(duplicates_map)

    duplicates_map.save("boston_duplicate_trips.html")
    print("Map saved to 'boston_duplicate_trips.html'")
