import os
import csv
import click
import cv2
import numpy as np
import pandas as pd
from pupil_apriltags import Detector

def detect_tags_with_area(image_path, detector, scale=0.5, min_area=500):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        return []

    image_small = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    inv_scale = 1.0 / scale

    tags_raw = detector.detect(image_small, estimate_tag_pose=False)

    selected_tags = []

    for tag in tags_raw:
        tag_id = tag.tag_id
        if tag_id not in {0, 1}:
            continue

        center = np.array(tag.center) * inv_scale
        corners = np.array(tag.corners) * inv_scale
        area = cv2.contourArea(corners.astype(np.float32))

        if area >= min_area:
            selected_tags.append({
                "id": tag_id,
                "center": center.tolist(),
                "area": float(area)
            })

    return selected_tags

@click.command()
@click.argument("input_folder", type=click.Path(exists=True))
@click.argument("output_csv", type=click.Path(writable=True))
@click.option("--scale", default=0.5)
@click.option("--min_area", default=4000)
def process_folder(input_folder, output_csv, scale, min_area):
    # DETECTOR PARAMS
    detector = Detector(
        families='tag16h5',
        nthreads=1,
        quad_decimate=1.0,
        quad_sigma=0.8,
        refine_edges=True,
        decode_sharpening=0.25,
        debug=False
    )

    results = []

    image_files = sorted([
        f for f in os.listdir(input_folder)
        if f.lower().endswith((".jpg"))
    ])

    for filename in image_files:
        path = os.path.join(input_folder, filename)
        tags = detect_tags_with_area(path, detector, scale=scale, min_area=min_area)

        tag0 = next((t for t in tags if t['id'] == 0), None)
        tag1 = next((t for t in tags if t['id'] == 1), None)

        row = {
            "filename": filename,
            "tag0_x": tag0["center"][0] if tag0 else None,
            "tag0_y": tag0["center"][1] if tag0 else None,
            "tag1_x": tag1["center"][0] if tag1 else None,
            "tag1_y": tag1["center"][1] if tag1 else None,
        }
        results.append(row)

    df = pd.DataFrame(results)
    df.to_csv(output_csv, index=False)
    print(f"SAVED : {output_csv}")

if __name__ == "__main__":
    process_folder()
