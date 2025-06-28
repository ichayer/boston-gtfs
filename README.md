# Public transport in Zurich using MobilityDB

## Load GTFS Scheduled Data in PostgresSQL

### Step 1 – Scheduled data to be used

We will use the Zurich GTFS timetable dataset for 2025, available at:

👉 [Zurich GTFS 2025 Timetable](https://data.stadt-zuerich.ch/dataset/vbz_fahrplandaten_gtfs/resource/4aa1c6c4-acc3-4b61-8fe7-221b3bd2fd03)

### Step 2 – Prepare the scheduled data

Inside the `scheduled/data` folder, you will find a .zip file that you must unzip. The archive contains several `.txt` files, such as:
- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`
- `transfers.txt`
- etc.

Each file contains structured information that defines how scheduled trips are organized and operated.
