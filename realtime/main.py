from collector.vehicle_data_collector import VehicleDataCollector


if __name__ == "__main__":
    collector = VehicleDataCollector(
        vehicle_protobuf_url="https://cdn.mbta.com/realtime/VehiclePositions.pb"
    )

    # By duration:
    df_duration = collector.collect_by_duration(duration_minutes=1, interval_seconds=10)

    # Or by number of changes:
    # df_changes = collector.collect_by_changes(max_changes=5, interval_seconds=10)

    # Save the DataFrame to a Parquet file
    df_duration.to_parquet("vehicles_by_duration.parquet")
