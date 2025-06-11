import click
import pandas as pd

@click.command()
@click.option('--exif', required=True, type=click.Path(exists=True), help='EXIF CSV file.')
@click.option('--rosbag', required=True, type=click.Path(exists=True), help='ROS bag CSV file.')
@click.option('--output', required=True, type=click.Path(writable=True), help='Output CSV file path.')
def merge_metadata(exif, rosbag, output):
    """Merge EXIF metadata and ROS bag GNSS data by timestamp."""
    exif_df = pd.read_csv(exif)
    rosbag_df = pd.read_csv(rosbag)

    # Apply correction to GPS Altitude from EXIF
    if 'GPS Altitude' in exif_df.columns:
        exif_df['GPS Altitude'] = exif_df['GPS Altitude'] - 16

    merged = pd.merge_asof(
        exif_df.sort_values('Date/Time Original'),
        rosbag_df.sort_values('time'),
        left_on="Date/Time Original",
        right_on="time",
        direction="nearest",
        tolerance=100_000_000
    )

    # Apply correction to alt column from ROS bag data
    if 'alt' in merged.columns:
        merged['alt'] = merged['alt'].apply(lambda x: max(0.0, x - 100))

    merged.to_csv(output, index=False)
    click.echo(f"MERGED TO: {output}")
    click.echo(merged.head().to_string(index=False))


if __name__ == '__main__':
    merge_metadata()
