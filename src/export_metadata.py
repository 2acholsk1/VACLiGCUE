import click
import pandas as pd
import re
import os
from datetime import datetime, timezone


def dms_to_decimal(degrees, minutes, seconds, direction):
    decimal = float(degrees) + float(minutes)/60 + float(seconds)/3600
    if direction in ["S", "W"]:
        decimal *= -1
    return decimal


def parse_exif_block(text):
    data = {}

    def extract(key, pattern=None, convert=None):
        match = re.search(f"{re.escape(key)}\s*:\s*(.*)", text)
        if match:
            value = match.group(1).strip()
            if pattern:
                sub_match = re.search(pattern, value)
                if sub_match:
                    value = sub_match.groups()
                else:
                    data[key] = None
                    return
            if convert:
                try:
                    value = convert(value)
                except Exception as e:
                    value = None
            data[key] = value
        else:
            data[key] = None


    extract("File Name")
    extract("Date/Time Original", convert=lambda date: int(
        datetime.strptime(date, "%Y:%m:%d %H:%M:%S")
        .replace(tzinfo=timezone.utc)
        .timestamp() * 1e9
    ))
    extract("Make")
    extract("Camera Model Name")
    extract("GPS Latitude",
        pattern=r"(\d+) deg (\d+)' ([\d.]+)\" (\w)",
        convert=lambda groups: dms_to_decimal(*groups))
    extract("GPS Longitude",
            pattern=r"(\d+) deg (\d+)' ([\d.]+)\" (\w)",
            convert=lambda groups: dms_to_decimal(*groups))
    extract("GPS Altitude", convert=lambda x: float(x.split()[0]))
    extract("Gimbal Yaw Degree", convert=float)
    extract("Gimbal Pitch Degree", convert=float)
    extract("Gimbal Roll Degree", convert=float)
    extract("Flight Yaw Degree", convert=float)
    extract("Flight Pitch Degree", convert=float)
    extract("Flight Roll Degree", convert=float)

    return data

@click.command()
@click.argument('folder', type=click.Path(exists=True))
@click.argument('output', type=click.Path(writable=True))
def process_exif_files(folder, output):
    all_data = []
    for filename in os.listdir(folder):
        if filename.lower().endswith('.txt'):
            with open(os.path.join(folder, filename), 'r', encoding='utf-8') as file:
                content = file.read()
                parsed = parse_exif_block(content)
                all_data.append(parsed)

    df = pd.DataFrame(all_data)
    df.to_csv(output, index=False)
    click.echo(f"SAVED: {output}")


if __name__ == '__main__':
    process_exif_files()
