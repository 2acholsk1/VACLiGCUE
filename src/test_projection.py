import pandas as pd
from PIL import Image
import cv2
import numpy as np
path = '../01_loop/'  # Adjust path as needed
df = pd.read_csv(path+'bbox.csv')  # Replace with actual path

# Iterate through rows
for idx, row in df.iterrows():
    filename = path + row['filename']
    pt1 = (row['x1'], row['x2'])
    pt2 = (row['x3'], row['x4'])
    pt3 = (row['y1'], row['y2'])
    pt4 = (row['y3'], row['y4'])
    pts = np.array([pt1, pt2, pt3, pt4], np.int32)
    center = np.mean(pts, axis=0).astype(int)  # Calculate center of bounding box
    lat = row['lat']
    lon = row['lon']

    # Load image
    try:
        image = Image.open(filename)
        print(f"Image: {filename}")
        
        print(f"  lat: {lat}, lon: {lon}")
        # Draw bounding box
        cv_image = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        for pt in pts:
            cv2.circle(cv_image, tuple(pt), 10, (255, 0, 0), -1)
        cv2.circle(cv_image, tuple(center), 20, (0, 0, 255), -1)  # Draw center point
        cv_image = cv2.resize(cv_image, (800, 600))  # Resize for better visibility
        cv2.imshow('Bounding Box', cv_image)
        cv2.waitKey(0)  # Wait for a key press to close the window
        cv2.destroyAllWindows()
        
        
    except FileNotFoundError:
        print(f"Image {filename} not found.")
