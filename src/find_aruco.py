import os
import time
import csv
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from dt_apriltags import Detector
from main import dms_to_decimal

# Configuration constants
IMG_DIR = Path("../")
CSV_PATH = Path("bbox.csv")
WIN_SIZE = 1500
STRIDE = 700

def intrinsic():
    K = np.array([[2720.51946242, 0, 2066.0622728],
              [0, 2726.34873667, 1543.55527727],
              [0, 0, 1]])

    # Distortion coefficients: k1, k2, p1, p2
    dist = np.array([0.06989963, -0.11571736, 0.00095562, 0.0022504])
    return K, dist

def loop_dirs(root: Path) -> list[Path]:
    """Return all sub‑directories of *root* that end with '_loop', sorted alphabetically."""
    return sorted(p for p in root.iterdir() if p.is_dir() and p.name.endswith("_loop"))

def list_images(directory: Path, extension: str = ".JPG"):
    """Return a sorted list of image paths with the given extension from *directory*."""
    return sorted(p for p in directory.iterdir() if p.suffix.upper() == extension.upper())


def init_detector():
    """Initialise and return an OpenCV ArUco/AprilTag detector."""
    dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_APRILTAG_16H5)
    params = cv2.aruco.DetectorParameters()
    params.adaptiveThreshWinSizeMin = 5
    params.adaptiveThreshWinSizeMax = 50
    params.adaptiveThreshWinSizeStep = 5
    params.minMarkerPerimeterRate = 0.05
    params.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX
    params.useAruco3Detection = True  # Improved accuracy
    return cv2.aruco.ArucoDetector(dictionary, params)


def write_csv_header(writer: csv.writer):
    header = ["filename", "object_id"] + [f"x{i+1}" for i in range(4)] + [f"y{i+1}" for i in range(4)]
    header += ["lat", "lon"]
    writer.writerow(header)


def detect_markers(image: np.ndarray, detector, win_size: int, stride: int):
    """Slide a window over *image* and detect markers. Return a dict[id] = corners."""
    detections = {}
    h, w = image.shape[:2]
    
    for y in range(0, h - win_size + 1, stride):
        for x in range(0, w - win_size + 1, stride):
            window = image[y : y + win_size, x : x + win_size]
            corners, ids, _ = detector.detectMarkers(window)
            if ids is not None:
                for i, marker_id in enumerate(ids.flatten()):
                    detections[int(marker_id)] = corners[i] + np.array([[x, y]])  # offset to full‑image coords
    return detections

from scipy.spatial.transform import Rotation as R
import navpy
import pymap3d as pm   #  pip install pymap3d

def log_and_draw_detections(image: np.ndarray, detections: dict, filename: str, writer: csv.writer, metadata):
    """Log detections to CSV and draw outlines/IDs on *image*. Return (front_corners, back_corners)."""
    front = back = None
    orientation, lat_drone, lon_drone, image_width, image_height, center_image, real_distance, fov, alt = telemetry(metadata)
    K, dist = intrinsic()
    for marker_id, corners in detections.items():
        corners_c = corners.squeeze(axis=0)
        center_obj = np.mean(corners[0], axis=0).astype(int)
        
        pixel_h = np.array([center_obj[0], center_obj[1], 1])
        ray_cam = np.linalg.inv(K) @ pixel_h
        ray_cam /= np.linalg.norm(ray_cam)
        
        R_cam_to_ned = R.from_euler('zyx', np.radians(orientation), degrees=False).as_matrix()
        ray_ned = R_cam_to_ned @ ray_cam
        p_ned_drone = np.array([lat_drone, lon_drone, alt]) # <------------- tu chyba trzeba zmienic na geodetic
        dz = ray_ned[2]
        z_ground = 0
        t = (z_ground - p_ned_drone[2]) / dz
        intersection_ned = p_ned_drone + t * ray_ned
        n, e, d = intersection_ned        # D is +Down
        lat, lon, h_gnd = pm.ned2geodetic(n, e, -d,   # -d → metres above ellipsoid
                                          p_ned_drone[0], p_ned_drone[1], p_ned_drone[2])
        # print(f"drone NED: {p_ned_drone}")
        # print(f"Intersection NED: {intersection_ned}")
        # print(f"Intersection Geodetic: {lat}, {lon}, {h_gnd}")
        
        # lat, lon = pixel_to_marker_positon(
        #     corners_c, real_distance, center_image, orientation[0], lat_drone, lon_drone
        # )
        # target = np.mean(corners_c, axis=0).astype(int)
        # lat, lon = pixel_to_latlon_with_size(
        #     target, real_distance, (corners_c[0], corners_c[1]),
        #     fov, image_width, image_height, gimbal_yaw, lat_drone, lon_drone
        # )
        # lat, lon = pixel_to_latlon_fov(
        #     corners_c[0], fov, image_width, image_height, alt, gimbal_yaw, lat_drone, lon_drone
        # )
        writer.writerow([filename, marker_id] + [int(c) for corner in corners[0] for c in corner]+ [lat, lon])
        cv2.polylines(image, [np.int32(corners)], True, (0, 255, 0), 2)
        cv2.putText(image, f"ID: {marker_id}", tuple(center_obj), cv2.FONT_HERSHEY_SIMPLEX, 3, (0, 0, 255), 10)
        if marker_id == 1:
            front = corners
        elif marker_id == 0:
            back = corners
    return front, back


def pixel_to_marker_positon(corners, real_distance, center_image, gimbal_yaw, lat_drone, lon_drone):
    uA, vA = corners[0][1], corners[0][0]
    uB, vB = corners[1][1], corners[1][0]
    distanse_pixel = np.sqrt((uB - uA) ** 2 + (vB - vA) ** 2)
    obj_center = np.mean(corners, axis=0)
    s = real_distance / distanse_pixel
    c_x = center_image[1]
    c_y = center_image[0]
    dx_cam = (obj_center[1] - c_x) * s
    dy_cam = (obj_center[0] - c_y) * s
    E = dx_cam * np.cos(np.radians(gimbal_yaw)) - dy_cam * np.sin(np.radians(gimbal_yaw))
    N = dx_cam * np.sin(np.radians(gimbal_yaw)) + dy_cam * np.cos(np.radians(gimbal_yaw))
    R = 6378137  # Earth radius in meters
    delta_lat = N / R
    delta_lon = E / (R * np.cos(np.radians(lat_drone)))
    theta_lat = lat_drone + delta_lat * (180 / np.pi)
    theta_lon = lon_drone + delta_lon * (180 / np.pi)
    return theta_lat, theta_lon

R_EARTH = 6378137.0  # m

def pixel_to_latlon_with_size(
    corner,          # (row, col) of your target pixel
    size_m,          # real-world marker length L (m)
    size_corners,    # two image corners defining that marker (for Δp)
    FOVx,            # horizontal field-of-view (deg)
    img_w, img_h,    # image size in pixels
    yaw_deg,         # gimbal yaw
    lat0, lon0       # drone GPS
):
    # --- 1) measure pixel span of your known-size marker ---
    (rA, cA), (rB, cB) = size_corners
    Δp = np.hypot(rB - rA, cB - cA)  # pixel distance between corners
    
    # --- 2) angular width of marker (rad) & slant range D ---
    α_obj = np.radians( (Δp / img_w) * FOVx )
    D = (size_m / 2.0) / np.tan(α_obj / 2.0)
    H = D   # assume nadir → vertical height ≈ slant distance
    
    # --- 3) now do the FOV→ENU conversion as before ---
    # 3.1 compute focal lengths
    fx = (img_w/2) / np.tan(np.radians(FOVx/2))
    FOVy = 2*np.degrees(np.arctan((img_h/img_w)*np.tan(np.radians(FOVx/2))))
    fy = (img_h/2) / np.tan(np.radians(FOVy/2))

    # 3.2 pixel → angles
    u, v     = corner[1], corner[0]
    cx, cy   = img_w/2, img_h/2
    αx = np.arctan((u - cx)/fx)
    αy = np.arctan((cy - v)/fy)

    # 3.3 angles → camera-frame meters (assuming flat ground)
    E_cam = H * np.tan(αx)
    N_cam = H * np.tan(αy)

    # 3.4 rotate by yaw into ENU
    ψ = np.radians(yaw_deg)
    E =  E_cam * np.cos(ψ) + N_cam * np.sin(ψ)
    N = -E_cam * np.sin(ψ) + N_cam * np.cos(ψ)

    # 3.5 ENU → Δlat/Δlon
    dlat = (N / R_EARTH) * (180/np.pi)
    dlon = (E / (R_EARTH * np.cos(np.radians(lat0)))) * (180/np.pi)

    return lat0 + dlat, lon0 + dlon

def pixel_to_latlon_fov(corner, FOVx, img_w, img_h, H, yaw_deg, lat0, lon0):
    # 1) focal lengths
    fx = (img_w/2) / np.tan(np.radians(FOVx/2))
    FOVy = 2*np.degrees(np.arctan((img_h/img_w)*np.tan(np.radians(FOVx/2))))
    fy = (img_h/2) / np.tan(np.radians(FOVy/2))

    # 2) pixel → angles
    u, v = corner[1], corner[0]
    cx, cy = img_w/2, img_h/2
    ax = np.arctan((u - cx) / fx)
    ay = np.arctan((cy - v) / fy)

    # 3) angles → ground offsets
    E_cam = H * np.tan(ax)
    N_cam = H * np.tan(ay)

    # 4) rotate by yaw into ENU
    ψ = np.radians(yaw_deg)
    E =  E_cam * np.cos(ψ) + N_cam * np.sin(ψ)
    N = -E_cam * np.sin(ψ) + N_cam * np.cos(ψ)

    # 5) project to lat/lon
    dlat = (N / R_EARTH) * (180/np.pi)
    dlon = (E / (R_EARTH * np.cos(np.radians(lat0)))) * (180/np.pi)

    return lat0 + dlat, lon0 + dlon

def draw_heading(image: np.ndarray, front_corners, back_corners):
    """Draw a heading arrow from back to front; return heading angle in degrees if both tags present."""
    if front_corners is None or back_corners is None:
        return None
    front_center = np.mean(front_corners[0], axis=0).astype(int)
    back_center = np.mean(back_corners[0], axis=0).astype(int)
    cv2.arrowedLine(image, tuple(back_center), tuple(front_center), (255, 0, 0), 10, tipLength=0.4)
    vec = front_center - back_center
    return np.degrees(np.arctan2(vec[1], vec[0]))

def telemetry(metadata):   
    gimbal_yaw = extract_number(metadata["Gimbal Yaw Degree"])
    gimbal_roll = extract_number(metadata["Gimbal Roll Degree"])
    gimbal_pitch = extract_number(metadata["Gimbal Pitch Degree"])
    lat_drone = parse_dms_string(metadata["GPS Latitude"])
    lon_drone = parse_dms_string(metadata["GPS Longitude"])
    image_width = int(metadata["Exif Image Width"])
    image_height = int(metadata["Exif Image Height"])
    fov = extract_number(metadata["Field Of View"])
    alt = extract_number(metadata["Absolute Altitude"])
    center_image = (image_height // 2, image_width // 2)
    real_distance = 0.56
    orientation = np.array([gimbal_yaw, gimbal_pitch, gimbal_roll])
    return orientation, lat_drone, lon_drone, image_width, image_height, center_image, real_distance, fov, alt

def process_image(img_path: Path, detector, writer: csv.writer, win_size=1500, stride=700, metadata=None):
    """Process a single image: detect markers, annotate, save CSV; return annotated image and heading angle."""
    pil_img = Image.open(img_path)
    image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    # image = cv2.undistort(image, K, dist)
    detections = detect_markers(image, detector, win_size, stride)
    front, back = log_and_draw_detections(image, detections, img_path.name, writer, metadata)
    angle = draw_heading(image, front, back)

    return image, angle, detections

def init_apriltag_detector():
    """Initialise and return an AprilTag detector."""
    return Detector(families="tag16h5", nthreads=4)
    # return Detector(families="tag16h5", nthreads=4, quad_decimate=1.0, quad_sigma=0.0,
    #                 refine_edges=True, decode_sharpening=0.25, debug=False)

keys = [
    "Gimbal Roll Degree", "Gimbal Yaw Degree", "Gimbal Pitch Degree",
    "Flight Roll Degree", "Flight Yaw Degree", "Flight Pitch Degree",
    "Absolute Altitude", "Relative Altitude", "Field Of View", "Focal Length",
    "GPS Position", "Shutter Speed", "GPS Latitude", "GPS Longitude", "Exif Image Width", "Exif Image Height"
]
def extract_info_from_txt(file_path):
    extracted = {}
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            for key in keys:
                if line.strip().startswith(key):
                    # Split at the first colon and strip spaces
                    value = line.split(":", 1)[1].strip() if ":" in line else ""
                    extracted[key] = value
    return extracted  

import re
def extract_number(text):
    match = re.search(r"[-+]?\d*\.\d+|\d+", text)
    return float(match.group()) if match else None

def parse_dms_string(dms_str):
    # Example input: "52 deg 24' 6.95\" N"
    match = re.match(r"(\d+)\s*deg\s*(\d+)'\s*([\d.]+)\"\s*([NSEW])", dms_str)
    if match:
        deg = int(match.group(1))
        min_ = int(match.group(2))
        sec = float(match.group(3))
        ref = match.group(4)
        return dms_to_decimal((deg, min_, sec), ref)
    else:
        raise ValueError(f"Invalid DMS format: {dms_str}")

def apriltag_process_image(img_path: Path, detector):
    pil_img = Image.open(img_path)
    image = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    tags = detector.detect(gray, estimate_tag_pose=False, camera_params=None, tag_size=None)
    return tags, image

def main():
    detector = init_detector()
    aprilltag_detector = init_apriltag_detector()
    for img_dir in loop_dirs(IMG_DIR):
        print(f"Processing directory: {img_dir.name}")
        image_files = list_images(img_dir)
        csv_path = img_dir / CSV_PATH
        img_dir = img_dir.with_name(img_dir.name + "_labeled")
        os.mkdir(img_dir) if not img_dir.exists() else None
        results = 0
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            write_csv_header(writer)

            for img_path in image_files:
                metadata_path = img_path.name[:-4]
                metadata_path = img_path.with_name("meta_" + img_path.name).with_suffix(".txt")
                metadata = extract_info_from_txt(metadata_path)
                start = time.time()
                annotated, angle, detections = process_image(img_path, detector, writer, WIN_SIZE, STRIDE, metadata)
                results += len(detections)
    
                # print(f"Detection took {time.time() - start:.2f} seconds")
                # if angle is not None:
                #     print(f"Heading angle for {img_path.name}: {angle:.2f} degrees")
                tags, image = apriltag_process_image(img_path, aprilltag_detector)

                pil_img = Image.open(img_path)
                image_color = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                tags = [tag for tag in tags if tag.tag_id in [0, 1]]
                for tag in tags:
                    for idx in range(len(tag.corners)):
                        cv2.line(image_color, tuple(tag.corners[idx-1, :].astype(int)), tuple(tag.corners[idx, :].astype(int)), (0, 255, 0))
                    # print(f"Detected tag ID: {tag.tag_id}, Corners: {tag.corners}")
                    
                    cv2.putText(image_color, str(tag.tag_id),
                                org=(tag.corners[0, 0].astype(int)+10,tag.corners[0, 1].astype(int)+10),
                                fontFace=cv2.FONT_HERSHEY_SIMPLEX,
                                fontScale=3,
                                thickness=10,
                                color=(0, 0, 255))
                # cv2.imshow("Annotated Image", cv2.resize(image_color, (1280, 720)))
                # cv2.waitKey(1)
                #save annotated image
                annotated_path = img_dir / f"annotated_{img_path.name[:-4]}_april.png"
                # cv2.imwrite(str(annotated_path), image_color)
        print(f"Processed {len(image_files)} images in {img_dir.name}")
        print("results", results/ (len(image_files)*2))
        print(f"Saved CSV to {csv_path} and annotated images to {img_dir}")

if __name__ == "__main__":
    main()
