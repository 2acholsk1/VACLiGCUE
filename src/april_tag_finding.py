import cv2
import numpy as np
from pupil_apriltags import Detector

def detect_tags_with_area(image_path, scale=0.5, visualize=True, min_area=500):
    image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise FileNotFoundError(f"PIC NOT FOUND: {image_path}")

    image_small = cv2.resize(image, (0, 0), fx=scale, fy=scale)
    inv_scale = 1.0 / scale

    detector = Detector(
        families='tag16h5',
        nthreads=2,
        quad_decimate=1.0,
        quad_sigma=0.8,
        refine_edges=True,
        decode_sharpening=0.25,
        debug=False
    )

    tags_raw = detector.detect(image_small, estimate_tag_pose=False)
    print(f"FOUND {len(tags_raw)} TAGS")

    selected_tags = []

    for tag in tags_raw:
        tag_id = tag.tag_id
        if tag_id not in {0, 1}:
            continue
        print('a')

        center = np.array(tag.center) * inv_scale
        corners = np.array(tag.corners) * inv_scale
        area = cv2.contourArea(corners.astype(np.float32))

        if area >= min_area:
            selected_tags.append({
                "id": tag_id,
                "center": center.tolist(),
                "corners": corners.tolist(),
                "area": float(area)
            })

    print(f"STOPPED {len(selected_tags)} MIN_AREA >= {min_area}")

    if visualize and selected_tags:
        image_vis = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
        for tag in selected_tags:
            center = np.array(tag["center"]).astype(int)
            corners = np.array(tag["corners"]).astype(int)

            for pt in corners:
                cv2.circle(image_vis, tuple(pt), 5, (0, 255, 0), 2)

            cv2.putText(image_vis, f"ID {tag['id']} ({int(tag['area'])})", tuple(center),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

        preview = cv2.resize(image_vis, (0, 0), fx=0.5, fy=0.5)
        cv2.imshow("AprilTag Detekcja", preview)
        cv2.waitKey(0)
        cv2.destroyAllWindows()

    return selected_tags

if __name__ == "__main__":
    tags = detect_tags_with_area(
        image_path="05_loop/DJI_20250513140029_0211_D.JPG",
        min_area=500
    )

    for tag in tags:
        print(f"Tag ID: {tag['id']}, area: {tag['area']:.1f}")

