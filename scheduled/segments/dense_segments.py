from gtfs_functions import Feed
from itertools import combinations
from collections import defaultdict
import pandas as pd
from keplergl import KeplerGl
import geopandas as gpd

if __name__ == "__main__":

    # --- Parameters ---
    gtfs_file = "data.zip"
    analysis_date = "2025-01-10"
    m = 10  # Minimum number of vehicles to consider a segment a hotspot in a time window
    n = 500  # Minimum number of shared hotspots for two routes to be considered overlapping
    time_windows = list(range(25))  # windows of 1 hour

    # --- Load GTFS and segment frequencies ---
    feed = Feed(
        gtfs_file,
        start_date=analysis_date,
        end_date=analysis_date,
        time_windows=time_windows,
    )
    segments_freq = feed.segments_freq

    # --- Filter hotspots (segments with at least m vehicles in the same time window) ---
    hotspots = segments_freq[
        (segments_freq["ntrips"] >= m) & (segments_freq["route_id"] != "ALL_LINES")
    ].copy()

    # --- Build a dictionary: route_id -> set of (segment_name, window) ---
    route_hotspot_segments = defaultdict(set)
    for _, row in hotspots.iterrows():
        route_key = row["route_id"]
        segment_window = (row["segment_name"], row["window"])
        route_hotspot_segments[route_key].add(segment_window)

    # --- Compare routes pairwise and compute overlap ---
    overlapping_routes = []
    for r1, r2 in combinations(route_hotspot_segments.keys(), 2):
        segs1 = route_hotspot_segments[r1]
        segs2 = route_hotspot_segments[r2]
        shared = segs1.intersection(segs2)

        if len(shared) >= n:
            overlapping_routes.append(
                {
                    "route_1": r1,
                    "route_2": r2,
                    "shared_hotspots": len(shared),
                    "shared_segment_windows": list(shared),
                }
            )

    # --- Output results ---
    if overlapping_routes:
        df_overlap = pd.DataFrame(overlapping_routes)
        df_overlap.rename(
            columns={"route_1": "route_1_id", "route_2": "route_2_id"}, inplace=True
        )

        # --- Print overlapping route pairs ---
        print("\n🔁 Overlapping route pairs:")
        for _, row in df_overlap.iterrows():
            print(
                f"Route {row['route_1_id']} overlaps with Route {row['route_2_id']} (shared hotspots: {row['shared_hotspots']})"
            )
    else:
        print("No overlapping routes found under the specified criteria.")

    # --- Visualize persistent hotspots only extracting all shared segments between overlapping routes ---
    all_shared_segments_windows = set()
    for entry in overlapping_routes:
        all_shared_segments_windows.update(entry["shared_segment_windows"])

    if all_shared_segments_windows:
        # Convert to DataFrame for filtering
        shared_df = pd.DataFrame(
            all_shared_segments_windows, columns=["segment_name", "window"]
        )
        persistent_hotspots = hotspots.merge(shared_df, on=["segment_name", "window"])
        persistent_hotspots = gpd.GeoDataFrame(persistent_hotspots, geometry="geometry")

        mapa = KeplerGl(height=600)
        mapa.add_data(data=persistent_hotspots, name="Persistent Hotspots")
        mapa.save_to_html(file_name="persistent_hotspots_map.html")

    else:
        print("⚠️ No persistent hotspots found to visualize.")
