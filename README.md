# Public transport in Zurich using MobilityDB 
Lorem Ipsum

## Load GTFS Data in PostgresSQL

### Step 1 – Download the GTFS Dataset

Download the official Zurich timetable GTFS dataset for 2025 from:

👉 [Zurich GTFS 2025 Timetable](https://data.stadt-zuerich.ch/dataset/vbz_fahrplandaten_gtfs/resource/4aa1c6c4-acc3-4b61-8fe7-221b3bd2fd03)

### Step 2 – Extract Files

Unzip the downloaded file. It will contain several `.txt` files such as:

- `agency.txt`
- `stops.txt`
- `routes.txt`
- `trips.txt`
- `stop_times.txt`
- `calendar.txt`
- `calendar_dates.txt`
- `transfers.txt`
- etc.

### Step 3 – Organize the Files

Move all `.txt` files into a subfolder within the repository. We recommend creating a folder named `txt` inside this repo.

### Step 4 – Create a database in PostgresSQL

```sql
CREATE DATABASE swiss_gtfs;
```

### Step 5 – Update and run the SQL Script

Open `load_data.sql` and update the following line to match the path to your `txt` folder:

```sql
base_path := 'path/to/your/folder/';
```

> [!IMPORTANT]  
> Make sure the path ends with a / (or \ on Windows)

You can run the updated .sql file once you’ve made the changes.