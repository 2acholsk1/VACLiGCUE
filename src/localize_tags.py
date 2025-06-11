import pandas as pd
import numpy as np
from pyproj import Transformer
from tqdm import tqdm

# === INTRINSIC CAMERA CALIBRATION ===
def load_intrinsics():
    fx, fy, cx, cy = 2720.51946242, 2726.34873667, 2066.0622728, 1543.55527727
    return np.array([[fx, 0, cx],
                     [0, fy, cy],
                     [0, 0, 1]])

# === GIMBAL ROTATION (NED) ===
def euler_to_rotmat_ned(yaw, pitch, roll):
    y, p, r = np.deg2rad([yaw, pitch, roll])
    Rz = np.array([[np.cos(y), -np.sin(y), 0],
                   [np.sin(y),  np.cos(y), 0],
                   [0, 0, 1]])
    Ry = np.array([[np.cos(p), 0, np.sin(p)],
                   [0, 1, 0],
                   [-np.sin(p), 0, np.cos(p)]])
    Rx = np.array([[1, 0, 0],
                   [0, np.cos(r), -np.sin(r)],
                   [0, np.sin(r),  np.cos(r)]])
    return Rz @ Ry @ Rx

# === GPS ↔ NED TRANSFORMS ===
def gps_to_ned(lat, lon, alt, origin, tf):
    x0, y0, z0 = tf.transform(origin[1], origin[0], origin[2])
    x, y, z = tf.transform(lon, lat, alt)
    dx, dy, dz = x - x0, y - y0, z - z0
    return np.array([dy, dx, -dz])

def ned_to_gps(ned_point, origin, tf):
    x0, y0, z0 = tf.transform(origin[1], origin[0], origin[2])
    dx, dy, dz = ned_point[1], ned_point[0], -ned_point[2]
    x, y, z = x0 + dx, y0 + dy, z0 + dz
    lon, lat, alt = tf.transform(x, y, z, direction='INVERSE')
    return lat, lon, alt

# === RAY INTERSECTION WITH GROUND ===
def pixel_to_world_gps(pixel, K, R_cam_to_ned, drone_ned, tf, origin):
    K_inv = np.linalg.inv(K)
    pix_h = np.array([pixel[0], pixel[1], 1.0])
    direction_cam = K_inv @ pix_h
    direction_ned = R_cam_to_ned @ direction_cam
    direction_ned /= np.linalg.norm(direction_ned)

    if direction_ned[2] == 0:
        return None

    t = -drone_ned[2] / direction_ned[2]
    tag_ned = drone_ned + t * direction_ned
    return ned_to_gps(tag_ned, origin, tf)

# === MAIN FUNCTION ===
def localize_tags_from_csv(csv_path, output_csv):
    df = pd.read_csv(csv_path)
    K = load_intrinsics()
    tf = Transformer.from_crs("epsg:4326", "epsg:4978", always_xy=True)
    origin = df[['GPS Latitude', 'GPS Longitude', 'GPS Altitude']].iloc[0].values

    results = []

    for _, row in tqdm(df.iterrows(), total=len(df)):
        try:
            yaw = row['Gimbal Yaw Degree']
            pitch = row['Gimbal Pitch Degree']
            roll = row['Gimbal Roll Degree']
            drone_gps = (row['GPS Latitude'], row['GPS Longitude'], row['GPS Altitude'])
            drone_ned = gps_to_ned(*drone_gps, origin, tf)
            R = euler_to_rotmat_ned(yaw, pitch, roll)

            for tag_id in [0, 1]:
                x_key = f'tag{tag_id}_x'
                y_key = f'tag{tag_id}_y'

                if pd.notna(row.get(x_key)) and pd.notna(row.get(y_key)):
                    pixel = [row[x_key], row[y_key]]
                    gps_pos = pixel_to_world_gps(pixel, K, R, drone_ned, tf, origin)

                    if gps_pos is not None:
                        tag_lat, tag_lon, _ = gps_pos
                        results.append({
                            "File Name": row["File Name"],
                            "tag_id": tag_id,
                            "tag_lat": tag_lat,
                            "tag_lon": tag_lon
                        })
        except Exception as e:
            print(f"WARNING {e}")

    pd.DataFrame(results).to_csv(output_csv, index=False)
    print(f"\n Zapisano tagi do: {output_csv}")

if __name__ == "__main__":
    localize_tags_from_csv("02_loop/input_data.csv", "02_loop/output_data.csv")
