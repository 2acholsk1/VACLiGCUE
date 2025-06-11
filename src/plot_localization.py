import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("02_loop/input_data.csv")

tags_df = pd.read_csv("02_loop/output_data.csv")

required = ['GPS Latitude', 'GPS Longitude', 'lat', 'lon']
if not all(col in df.columns for col in required):
    raise ValueError("Brakuje kolumn: 'GPS Latitude', 'GPS Longitude', 'lat', 'lon'")

tag_required = ['tag_lat', 'tag_lon', 'tag_id']
if not all(col in tags_df.columns for col in tag_required):
    raise ValueError("Brakuje kolumn z tagami: 'tag_lat', 'tag_lon', 'tag_id'")

plt.figure(figsize=(12, 8))

plt.plot(df['GPS Longitude'], df['GPS Latitude'], label='Drone (EXIF)', marker='o', markersize=3, linestyle='-', alpha=0.7)
plt.plot(df['lon'], df['lat'], label='Vehicle (ROS Bag)', marker='x', markersize=3, linestyle='-', alpha=0.7)
for tag_id in sorted(tags_df['tag_id'].unique()):
    subset = tags_df[tags_df['tag_id'] == tag_id]
    plt.scatter(subset['tag_lon'], subset['tag_lat'], s=60, label=f'AprilTag ID {int(tag_id)}', marker='s')

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Drone vs Vehicle Trajectories + AprilTag Positions')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.tight_layout()
plt.show()
