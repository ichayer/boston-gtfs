import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import os
from clients.postgres.postgres_client import PostgresClient


def plot_speed_diff_histogram(
    df: pd.DataFrame,
    output_path: str,
    bin_width: float = 1.0,
    bin_range: tuple = (-30, 30),
    xtick_interval: int = 2,
):
    df["speed_diff"] = df["real_avg_speed"] - df["scheduled_avg_speed"]

    # Generate bins based on input parameters
    bins = np.arange(bin_range[0], bin_range[1] + bin_width, bin_width)

    fig, ax = plt.subplots(figsize=(12, 6))
    counts, bins, patches = ax.hist(df["speed_diff"], bins=bins, edgecolor="white")

    # Color bars based on sign of speed difference
    for patch, left in zip(patches, bins):
        if left < 0:
            patch.set_facecolor("#ff7f7f")
        elif left > 0:
            patch.set_facecolor("#7fc97f")
        else:
            patch.set_facecolor("#cccccc")

    ax.set_title("Distribution of speed differences", fontsize=14)
    ax.set_xlabel("Speed Difference (km/h)", fontsize=12)
    ax.set_ylabel("Number of Segments", fontsize=12)
    ax.set_xticks(np.arange(bin_range[0], bin_range[1] + 1, xtick_interval))
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    plt.close()


if __name__ == "__main__":
    query = """
    SELECT
        real_avg_speed,
        scheduled_avg_speed
    FROM avg_speed_diff_per_segment
    """

    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    df = pg.query(query)
    output_file = "speed_diff_histogram.png"
    plot_speed_diff_histogram(
        df,
        output_path="speed_diff_histogram.png",
        bin_width=2,
        bin_range=(-20, 20),
        xtick_interval=2,
    )
