import click
import pandas as pd
from pathlib import Path
from rosbags.rosbag2 import Reader
from rosbags.serde import deserialize_cdr

TOPICS_TO_EXTRACT = {
    '/sensing/gnss/ublox_moving_base_node/fix': 'NavSatFix',
}

@click.command()
@click.argument('bag_path', type=click.Path(exists=True, file_okay=False))
@click.option('--output-dir', '-o', type=click.Path(file_okay=False, writable=True), default='.', help='Directory to save output CSV files.')
@click.option('--prefix', '-p', default='', help='Optional prefix for output filenames.')
def extract_rosbag_data(bag_path, output_dir, prefix):
    bag_path = Path(bag_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    with Reader(bag_path) as reader:
        for topic, typename in TOPICS_TO_EXTRACT.items():
            connections = [c for c in reader.connections if c.topic == topic]
            if not connections:
                click.echo(f"[WARN] Topic not found: {topic}")
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
                    click.echo(f"[SKIP] No parser for type: {typename}")
                    continue

            if data:
                df = pd.DataFrame(data)
                df['time'] = df['time'] + 7_200_000_000_000
                basename = topic.split('/')[-1] or 'topic'
                filename = f"{prefix}_{basename}.csv" if prefix else f"{basename}.csv"
                outpath = output_dir / filename
                df.to_csv(outpath, index=False)
                click.echo(f"[OK] Saved: {outpath}")

if __name__ == '__main__':
    extract_rosbag_data()
