# Public transport in Zurich using MobilityDB

## Load GTFS Scheduled Data in PostgresSQL

### Step 1 – Scheduled data to be used

We will use the Zurich GTFS timetable dataset for 2025 (`.zip` format), available at:

👉 [Zurich GTFS 2025 Timetable](https://data.stadt-zuerich.ch/dataset/vbz_fahrplandaten_gtfs/resource/4aa1c6c4-acc3-4b61-8fe7-221b3bd2fd03)

### Step 2 – Prepare the scheduled data

Inside the `scheduled/data` folder, unzip the previously downloaded `.zip` file. This will generate a new folder containing several `.txt` files, such as:

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`
- `transfers.txt`
- etc.

Each of these files contains structured information used to define how scheduled trips are organized and operated.

> [!TIP]  
> After unzipping, move all the `.txt` files **directly** into the `scheduled/data` folder. Do **not** leave them inside the subfolder that was automatically created during extraction.