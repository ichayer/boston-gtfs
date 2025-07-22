-- Setup
DROP TABLE IF EXISTS route_count_grid;
DROP TABLE IF EXISTS trips_active_restricted;

-- Make a grid to analyze
CREATE TABLE route_count_grid (
    i          BIGINT NOT NULL,
    j          BIGINT NOT NULL,
    geom       GEOMETRY NOT NULL,
    trip_count BIGINT,
    trip_ids   TEXT[],
    PRIMARY KEY (i, j)
);

-- Fill the table with a grid covering the boston land administrative areas
WITH area_to_analyze AS (
    SELECT ST_Union(geom) AS geom
    FROM townssurvey_poly
    WHERE town = 'BOSTON' AND island = 0
),
grid_full AS (
    SELECT geom, i, j
    FROM ST_SquareGrid(
        750,
        (SELECT a.geom FROM area_to_analyze a)
    ) AS sg(geom, i, j)
)
INSERT INTO route_count_grid (i, j, geom)
SELECT g.i, g.j, g.geom
FROM grid_full g, area_to_analyze a
WHERE ST_Intersects(g.geom, a.geom)
;

-- Index the grid spatially to accelerate future operations
CREATE INDEX grid_geom_gist_idx ON route_count_grid USING GIST (geom);

-- Create a view of the trips active during Thursday 10th of July 2025, restricting it between 15:00 and 16:00
CREATE TABLE trips_active_restricted AS (
    SELECT
        t.*,
        ST_Union(ST_Transform(ST_SetSRID(s.geometry, 4326), 26986)) AS geom_restricted
    FROM trips t
        JOIN stop_times st ON t.trip_id = st.trip_id
        JOIN segments s ON s.route_id = t.route_id AND s.start_stop_id = st.stop_id
        JOIN calendar c ON c.service_id = t.service_id
    WHERE
    st.departure_time >= '15:00'::interval AND st.arrival_time <= '16:00'::interval
    AND '2025-07-10'::date >= c.start_date AND '2025-07-10'::date <= c.end_date
    AND c.thursday::text = 'available'
    GROUP BY t.trip_id
);


-- For each cell on that grid, see how many trips pass through that cell
UPDATE route_count_grid g SET (trip_count, trip_ids) = (
    SELECT
        COUNT(*),
        ARRAY_AGG(t.trip_id)
    FROM trips_active_restricted t
    WHERE ST_Intersects(g.geom, t.geom_restricted)
);