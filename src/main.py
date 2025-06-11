from PIL import Image, ExifTags
import pandas as pd
import numpy as np
from datetime import datetime, timezone
import re
from pathlib import Path

def dms_to_decimal(dms, ref):
    deg, min_, sec = dms
    decimal = deg + min_ / 60 + sec / 3600
    return -decimal if ref in ['S', 'W'] else decimal

def extract_metadata(image_path):
    img = Image.open(image_path)
    name = image_path.name
    exif_data = img._getexif()
    if not exif_data:
        return None

    lat = lon = date = timestamp = None

    for tag_id, value in exif_data.items():
        tag = ExifTags.TAGS.get(tag_id, tag_id)
        match tag:
            case 'GPSInfo':
                lat = dms_to_decimal(value[2], value[1])
                lon = dms_to_decimal(value[4], value[3])
                alt = value[6]
            case 'DateTime':
                date = value
                dt = datetime.strptime(date, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
                timestamp = int(dt.timestamp() * 1e9)

    if None in [lat, lon, date, timestamp]:
        return None

    return {
        "PhotoName": name,
        "PhotoDate": date,
        "PhotoTimestamp": timestamp,
        "DroneLatitude": np.float64(lat),
        "DroneLongitude": np.float64(lon),
        "DroneAltitude": np.float64(alt)
    }

def extract_all_from_folder(folder_path):
    folder = Path(folder_path)
    images = list(folder.glob("*.JPG"))

    def extract_index(path):
        match = re.search(r'_(\d+)_D\.JPG$', path.name)
        return int(match.group(1)) if match else float('inf')

    images.sort(key=extract_index)

    all_data = []
    for img_path in images:
        result = extract_metadata(img_path)
        if result:
            result["Index"] = extract_index(img_path)
            all_data.append(result)

    df = pd.DataFrame(all_data)
    return df

df = extract_all_from_folder("09_loop")
print(df.head())
df.to_csv("09_loop/drone_metadata.csv", index=False)
