import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from realtime.clients.postgres.postgres_client import PostgresClient


def plot_speed_diff_histogram(
    df: pd.DataFrame,
    output_path: str = "speed_diff_histogram.png",
    bin_width: float = 2.0,
    bin_range: tuple = (-20, 20),
    xtick_interval: float = 2.0,
):
    # Calculate speed difference
    df["speed_diff"] = df["real_avg_speed"] - df["scheduled_avg_speed"]

    # Generate bin edges
    bins = np.arange(bin_range[0], bin_range[1] + bin_width, bin_width)

    # Plot histogram
    fig, ax = plt.subplots(figsize=(12, 6))
    counts, bin_edges, patches = ax.hist(df["speed_diff"], bins=bins, edgecolor="white")

    # Color bars based on sign of the bin center
    for patch, left, right in zip(patches, bin_edges[:-1], bin_edges[1:]):
        center = (left + right) / 2
        if center < 0:
            patch.set_facecolor("#ff7f7f")  # red
        elif center > 0:
            patch.set_facecolor("#7fc97f")  # green
        else:
            patch.set_facecolor("#cccccc")  # gray

    # Styling
    ax.set_title("Distribution of speed differences")
    ax.set_xlabel("Speed Difference (km/h)")
    ax.set_ylabel("Number of Segments")
    ax.set_xticks(np.arange(bin_range[0], bin_range[1] + 1, xtick_interval))
    ax.grid(axis="y", linestyle="--", alpha=0.7)

    # Save and show
    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()
    print(f"Histogram saved to {output_path}")


if __name__ == "__main__":
    pg = PostgresClient(
        db_user="postgres",
        db_pass="postgres",
        db_host="localhost",
        db_port="5432",
        db_name="mbtagtfs",
    )

    df = pg.query(
        sql="""
            SELECT
                real_avg_speed,
                scheduled_avg_speed
            FROM avg_speed_diff_per_segment 
            """
    )

    plot_speed_diff_histogram(
        df,
        output_path="speed_diff_histogram.png",
        bin_width=2,
        bin_range=(-20, 20),
        xtick_interval=2,
    )
