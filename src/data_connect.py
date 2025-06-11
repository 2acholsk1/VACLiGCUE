import click
import pandas as pd

@click.command()
@click.option('--exif', required=True, type=click.Path(exists=True))
@click.option('--rosbag', required=True, type=click.Path(exists=True))
@click.option('--tags', required=True, type=click.Path(exists=True))
@click.option('--output', required=True, type=click.Path(writable=True))
def merge_metadata(exif, rosbag, tags, output):
    exif_df = pd.read_csv(exif)
    rosbag_df = pd.read_csv(rosbag)
    tags_df = pd.read_csv(tags)

    # GPS FROM EXIF CHECK
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

    #ALTITUDE ROSBAG CHECK
    if 'alt' in merged.columns:
        merged['alt'] = merged['alt'].apply(lambda x: max(0.0, x - 100))

    merged = pd.merge(
        merged,
        tags_df,
        how='left',
        left_on='File Name',
        right_on='filename'
    ).drop(columns=['filename'], errors='ignore')

    merged.to_csv(output, index=False)
    click.echo(f"MERGED TO: {output}")
    click.echo(merged.head().to_string(index=False))


if __name__ == '__main__':
    merge_metadata()
