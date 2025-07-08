# --- PostgreSQL connection configuration ---
$env:PGUSER = "postgres"
$env:PGPASSWORD = "postgres"  # Replace with your PostgreSQL password
$env:PGHOST = "localhost"
$env:PGPORT = "5432"

# --- Step 1: Drop and create the database ---
$databaseName = "zurichpublictransport"
Write-Output "Dropping database '$databaseName' if it exists..."
psql -d postgres -c "DROP DATABASE IF EXISTS $databaseName;"

Write-Output "Creating database '$databaseName'..."
psql -d postgres -c "CREATE DATABASE $databaseName;"

# --- Step 2: Set database as active target ---
$env:PGDATABASE = $databaseName

# --- Step 3: Import GTFS data from txt files ---
# Assumes you are inside the folder where gtfs/*.txt files are located
Write-Output "Importing GTFS data into database '$databaseName'..."
npm exec -- gtfs-to-sql --require-dependencies -- $(Get-ChildItem -Path "gtfs" -Filter *.txt | ForEach-Object { "gtfs/$($_.Name)" }) | psql -b