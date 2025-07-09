import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

if __name__ == "__main__":
    # Connect to the database (adjust credentials as needed)
    db_user = "postgres"
    db_pass = "postgres"
    db_host = "localhost"
    db_port = "5432"
    db_name = "mbtagtfs"

    # 5. Create SQLAlchemy connection URL
    db_url = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
    engine = create_engine(db_url)

    starting_date = "2025-06-30"
    ending_date = "2025-07-06"

    # Define the SQL query
    query = f"""
        SELECT
            CASE EXTRACT(DOW FROM t_arrival AT TIME ZONE 'America/New_York')
                WHEN 0 THEN 'Weekend'
                WHEN 6 THEN 'Weekend'
                ELSE 'Weekday'
            END AS day_type,
            EXTRACT(HOUR FROM t_arrival AT TIME ZONE 'America/New_York') AS hour,
            COUNT(*) AS num_segments,
            AVG(speed) AS avg_speed
        FROM segment_speed_kmh_junejuly
        WHERE t_arrival >= '{starting_date} 00:00:00 America/New_York'
          AND t_arrival <  '{ending_date} 00:00:00 America/New_York'
        GROUP BY day_type, hour
        ORDER BY day_type, hour;
    """

    # Execute the query
    df = pd.read_sql(query, engine)

    # Ensure all 24 hours are present
    full_hours = pd.Series(range(24), name="hour")

    for day_type in ["Weekday", "Weekend"]:
        day_df = df[df["day_type"] == day_type].copy()
        day_df["hour"] = day_df["hour"].astype(int)

        # Fill in missing hours with zeros
        day_df = full_hours.to_frame().merge(day_df, on="hour", how="left")
        day_df["day_type"] = day_type
        day_df["num_segments"] = day_df["num_segments"].fillna(0).astype(int)
        day_df["avg_speed"] = day_df["avg_speed"].fillna(0)

        total_segments = day_df["num_segments"].sum()

        # Plot
        plt.figure(figsize=(10, 6))
        plt.bar(day_df["hour"], day_df["avg_speed"], color="green")
        plt.title(
            f"{day_type} - Average Speed by Hour\n{total_segments} segments considered\n from {starting_date} to {ending_date}"
        )
        plt.xlabel("Hour of Day")
        plt.ylabel("Average Speed (km/h)")
        plt.xticks(range(24))
        plt.grid(axis="y", linestyle="--", alpha=0.5)
        plt.tight_layout()
        plt.savefig(f"speed_{day_type.lower()}.png")
        plt.close()
        print(f"Saved: speed_{day_type.lower()}.png")

    # Combine both in one plot
    pivot_df = df.copy()
    pivot_df["hour"] = pivot_df["hour"].astype(int)
    pivot_df = pivot_df.pivot(
        index="hour", columns="day_type", values="avg_speed"
    ).fillna(0)

    plt.figure(figsize=(10, 6))
    plt.plot(pivot_df.index, pivot_df["Weekday"], label="Weekday", marker="o")
    plt.plot(pivot_df.index, pivot_df["Weekend"], label="Weekend", marker="o")
    plt.title(
        f"Average Speed by Hour - Weekday vs Weekend \n from {starting_date} to {ending_date}"
    )
    plt.xlabel("Hour of Day")
    plt.ylabel("Average Speed (km/h)")
    plt.xticks(range(24))
    plt.grid(axis="y", linestyle="--", alpha=0.5)
    plt.ylim(bottom=0)
    plt.legend()
    plt.tight_layout()
    plt.savefig("speed_comparison_weekday_vs_weekend.png")
    plt.close()
    print("Saved: speed_comparison_weekday_vs_weekend.png")
