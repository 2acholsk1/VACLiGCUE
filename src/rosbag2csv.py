from rosbags.rosbag2 import Reader
from rosbags.serde import deserialize_cdr
import pandas as pd

bag_path = 'rosbags/rosbag2_2025_05_13-13_51_41'

topics_to_extract = {
    '/sensing/gnss/ublox_moving_base_node/fix': 'NavSatFix',
    '/sensing/imu/imu_data': 'Imu',
    '/sensing/gnss/ublox_moving_base_node/fix_velocity': 'TwistWithCovarianceStamped',
}

with Reader(bag_path) as reader:
    for topic, typename in topics_to_extract.items():
        connections = [c for c in reader.connections if c.topic == topic]
        if not connections:
            print(f"[WARN] Topic {topic} not found.")
            continue

        data = []

        for conn, timestamp, rawdata in reader.messages(connections=connections):
            msg = deserialize_cdr(rawdata, conn.msgtype)

            if typename == 'NavSatFix':
                data.append({
                    'time': timestamp,
                    'lat': msg.latitude,
                    'lon': msg.longitude,
                    'alt': msg.altitude,
                })

            elif typename == 'Imu':
                data.append({
                    'time': timestamp,
                    'ang_vel_x': msg.angular_velocity.x,
                    'ang_vel_y': msg.angular_velocity.y,
                    'ang_vel_z': msg.angular_velocity.z,
                    'lin_acc_x': msg.linear_acceleration.x,
                    'lin_acc_y': msg.linear_acceleration.y,
                    'lin_acc_z': msg.linear_acceleration.z,
                })

            elif typename == 'TwistWithCovarianceStamped':
                data.append({
                    'time': timestamp,
                    'vx': msg.twist.twist.linear.x,
                    'vy': msg.twist.twist.linear.y,
                    'vz': msg.twist.twist.linear.z,
                    'wx': msg.twist.twist.angular.x,
                    'wy': msg.twist.twist.angular.y,
                    'wz': msg.twist.twist.angular.z,
                })

            else:
                print(f"[SKIP] No parser for type {typename}")
                continue

        if data:
            df = pd.DataFrame(data)
            df['time'] = df['time'] + 7_200_000_000_000
            basename = topic.split('/')[-1] or 'topic'
            outpath = f"{basename}_1351.csv"
            df.to_csv(outpath, index=False)
            print(f"[OK] Saved: {outpath}")
