import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("05_loop/full_data.csv")

required_columns = ['GPS Latitude', 'GPS Longitude', 'lat', 'lon']
if not all(col in df.columns for col in required_columns):
    raise ValueError("Missing one or more required columns: 'GPS Latitude', 'GPS Longitude', 'lat', 'lon'")

# Tworzenie wykresu
plt.figure(figsize=(10, 6))
plt.plot(df['GPS Longitude'], df['GPS Latitude'], label='EXIF (Drone)', marker='o', markersize=3)
plt.plot(df['lon'], df['lat'], label='ROSBAG (GNSS)', marker='x', markersize=3)

plt.xlabel('Longitude')
plt.ylabel('Latitude')
plt.title('Trajectory Comparison: Drone (EXIF) vs Vehicle (ROS Bag)')
plt.legend()
plt.grid(True)
plt.axis('equal')
plt.tight_layout()
plt.show()
