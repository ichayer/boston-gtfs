DROP TABLE IF EXISTS high_traffic_trips_with_stops_geom;

CREATE TABLE high_traffic_trips_with_stops_geom AS (
    WITH trip_id_arrays AS (
        SELECT trip_ids FROM route_count_grid ORDER BY trip_count DESC LIMIT 5
    ),
    cte AS (
        SELECT
            t.*,
            ST_Collect(ST_Transform(ST_SetSRID(s.stop_loc, 4326)::geometry, 26986)) AS stops_geom
        FROM trips t
            JOIN stop_times st ON t.trip_id = st.trip_id
            JOIN stops s ON s.stop_id = st.stop_id
        WHERE t.trip_id IN (SELECT unnest(trip_ids) FROM trip_id_arrays)
        GROUP BY t.trip_id
    )
    SELECT
        cte.*,
        ST_Buffer(cte.stops_geom, 750) AS stops_geom_buffer,
        ST_Area(ST_Buffer(cte.stops_geom, 750)) AS stops_geom_buffer_area
    FROM cte
);

CREATE INDEX traffic_trips_with_stops_geom_idx ON high_traffic_trips_with_stops_geom USING GIST (stops_geom_buffer);


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
        t1.stops_geom AS trip1_stops_geom,
        t2.stops_geom AS trip2_stops_geom,
        t1.stops_geom_buffer AS trip1_stops_geom_buffer,
        t2.stops_geom_buffer AS trip2_stops_geom_buffer,
        t1.stops_geom_buffer_area AS trip1_stops_geom_buffer_area,
        t2.stops_geom_buffer_area AS trip2_stops_geom_buffer_area,
        ST_Intersection(t1.stops_geom_buffer, t2.stops_geom_buffer) AS buffer_intersection,
        ST_Area(ST_Intersection(t1.stops_geom_buffer, t2.stops_geom_buffer)) AS buffer_intersection_area,
        sa1.shape AS trip1_shape,
        sa2.shape AS trip2_shape
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
;
