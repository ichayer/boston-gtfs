-- https://gtfs.org/documentation/schedule/reference/#agencytxt
DROP TABLE IF EXISTS agency CASCADE;
CREATE TABLE agency
(
    agency_id       TEXT PRIMARY KEY,
    agency_name     TEXT NOT NULL,
    agency_url      TEXT NOT NULL,
    agency_timezone TEXT NOT NULL,
    agency_lang     TEXT,
    agency_phone    TEXT
);

-- https://gtfs.org/documentation/schedule/reference/#calendartxt
DROP TABLE IF EXISTS calendar CASCADE;
CREATE TABLE calendar
(
    service_id TEXT PRIMARY KEY,
    monday     INTEGER,
    tuesday    INTEGER,
    wednesday  INTEGER,
    thursday   INTEGER,
    friday     INTEGER,
    saturday   INTEGER,
    sunday     INTEGER,
    start_date DATE,
    end_date   DATE
);

-- https://gtfs.org/documentation/schedule/reference/#calendar_datestxt
DROP TABLE IF EXISTS calendar_dates CASCADE;
CREATE TABLE calendar_dates
(
    service_id     TEXT    NOT NULL,
    date           DATE    NOT NULL,
    exception_type INTEGER NOT NULL,
    PRIMARY KEY (service_id, date),
    FOREIGN KEY (service_id) REFERENCES calendar (service_id)
);

-- https://gtfs.org/documentation/schedule/reference/#shapestxt
DROP TABLE IF EXISTS shapes CASCADE;
CREATE TABLE shapes
(
    shape_id            TEXT             NOT NULL,
    shape_pt_lat        DOUBLE PRECISION NOT NULL,
    shape_pt_lon        DOUBLE PRECISION NOT NULL,
    shape_pt_sequence   INTEGER          NOT NULL,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (shape_id, shape_pt_sequence)
);

-- https://gtfs.org/documentation/schedule/reference/#routestxt
DROP TABLE IF EXISTS routes CASCADE;
CREATE TABLE routes
(
    route_id         TEXT PRIMARY KEY,
    agency_id        TEXT, -- No reference because its only one agency
    route_short_name TEXT    NOT NULL,
    route_long_name  TEXT    NOT NULL,
    route_type       INTEGER NOT NULL,
    route_color      TEXT,
    route_text       TEXT
);

-- https://gtfs.org/documentation/schedule/reference/#stopstxt
DROP TABLE IF EXISTS stops CASCADE;
CREATE TABLE stops
(
    stop_id        TEXT PRIMARY KEY,
    stop_name      TEXT NOT NULL,
    stop_lat       DOUBLE PRECISION,
    stop_lon       DOUBLE PRECISION,
    stop_url       TEXT,
    location_type  TEXT,
    parent_station TEXT
);

-- https://gtfs.org/documentation/schedule/reference/#tripstxt
DROP TABLE IF EXISTS trips CASCADE;
CREATE TABLE trips
(
    route_id      TEXT NOT NULL,
    service_id    TEXT NOT NULL,
    trip_id       TEXT PRIMARY KEY,
    shape_id      TEXT NOT NULL,
    trip_headsign TEXT,
    direction_id  INTEGER,
    block_id      TEXT,
    FOREIGN KEY (route_id) REFERENCES routes (route_id),
    FOREIGN KEY (service_id) REFERENCES calendar (service_id)
);

-- https://gtfs.org/documentation/schedule/reference/#stop_timestxt
DROP TABLE IF EXISTS stop_times CASCADE;
CREATE TABLE stop_times
(
    trip_id             TEXT    NOT NULL,
    arrival_time        TEXT    NOT NULL,
    departure_time      TEXT    NOT NULL,
    stop_id             TEXT    NOT NULL,
    stop_sequence       INTEGER NOT NULL,
    stop_headsign       TEXT,
    pickup_type         INTEGER,
    drop_off_type       INTEGER,
    shape_dist_traveled DOUBLE PRECISION,
    PRIMARY KEY (trip_id, stop_sequence),
    FOREIGN KEY (trip_id) REFERENCES trips (trip_id),
    FOREIGN KEY (stop_id) REFERENCES stops (stop_id)
);

-- https://gtfs.org/documentation/schedule/reference/#transferstxt
DROP TABLE IF EXISTS transfers CASCADE;
CREATE TABLE transfers
(
    from_stop_id      TEXT,
    to_stop_id        TEXT,
    transfer_type     INTEGER,
    min_transfer_time INTEGER,

    FOREIGN KEY (from_stop_id) REFERENCES stops (stop_id),
    FOREIGN KEY (to_stop_id) REFERENCES stops (stop_id)
);

DO
$$
    DECLARE
        base_path TEXT := 'YOUR_PATH';
    BEGIN
        EXECUTE format(
                'COPY agency FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'agency.txt'
                );

        EXECUTE format(
                'COPY calendar FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'calendar.txt'
                );

        EXECUTE format(
                'COPY shapes FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'shapes.txt'
                );

        EXECUTE format(
                'COPY calendar_dates FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'calendar_dates.txt'
                );

        EXECUTE format(
                'COPY routes FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'routes.txt');

        EXECUTE format(
                'COPY stops FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'stops.txt'
                );

        EXECUTE format(
                'COPY trips FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'trips.txt'
                );

        EXECUTE format(
                'COPY stop_times FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'stop_times.txt');

        EXECUTE format(
                'COPY transfers FROM %L WITH (FORMAT csv, HEADER, DELIMITER '','', QUOTE ''"'')',
                base_path || 'transfers.txt'
                );

        -- Stops update
        ALTER TABLE stops
            ALTER COLUMN location_type TYPE INTEGER USING COALESCE(NULLIF(location_type, ''), '0')::INTEGER;

        -- Routes update
        UPDATE routes
        SET agency_id = (SELECT agency_id FROM agency LIMIT 1);

        ALTER TABLE routes
            ADD CONSTRAINT fk_routes_agency
                FOREIGN KEY (agency_id)
                    REFERENCES agency (agency_id);
    END
$$;