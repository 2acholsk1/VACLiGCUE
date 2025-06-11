import pandas as pd

photos = pd.read_csv("09_loop/drone_metadata.csv")
rosbag = pd.read_csv("fix_1351.csv")

merged = pd.merge_asof(
    photos,
    rosbag,
    left_on="PhotoTimestamp",
    right_on="time",
    direction="nearest",
    tolerance=500_000_000
)

merged.to_csv("09_loop/drone_car.csv", index=False)
print(merged.head())
