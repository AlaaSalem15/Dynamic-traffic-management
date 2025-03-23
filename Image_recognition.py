import cv2
import numpy as np
import torch
import matplotlib.pyplot as plt
from ultralytics import YOLO
from collections import Counter  # For counting detected objects

# ---------------------------------------------------------------------------------
# Load the YOLOv8 model for real-time object detection.
yolo_model = YOLO("yolov8n.pt")

# ---------------------------------------------------------------------------------
# Define a mapping from COCO class IDs to descriptive object names.
# We focus on traffic-related objects:
#   0: person -> pedestrian
#   1: bicycle -> cyclist
#   2: car
#   3: motorbike
#   5: bus
#   7: truck
#  80: emergency_vehicle
object_classes = {
    0: "pedestrian",
    1: "cyclist",
    2: "car",
    3: "motorbike",
    5: "bus",
    7: "truck",
    80: "emergency_vehicle"
}

# ---------------------------------------------------------------------------------
# Assign distinct BGR colors for each object type.
colors = {
    "pedestrian": (255, 0, 0),       # Blue
    "cyclist": (0, 255, 255),        # Yellow
    "car": (0, 255, 0),              # Green
    "motorbike": (255, 0, 255),      # Magenta
    "bus": (255, 255, 0),            # Cyan
    "truck": (0, 165, 255),          # Orange
    "emergency_vehicle": (0, 0, 255) # Red
}

# ---------------------------------------------------------------------------------
# Open the video file containing traffic footage.
video_path = "traffic_video.mp4" #current name, change based on video
traffic_video = cv2.VideoCapture(video_path)

# Define a congestion threshold.
# If the number of detected vehicles (excluding pedestrians and cyclists)
# exceeds this threshold, traffic is considered congested.
congestion_threshold = 20

# ---------------------------------------------------------------------------------
# Define text settings for better readability.
label_font_scale = 0.2      # For object labels
label_thickness = 1
status_font_scale = 1     # For traffic status text
status_thickness = 1
legend_font_scale = 0.4    # For the legend key
legend_thickness = 1

# ---------------------------------------------------------------------------------
# Process the video frame by frame.
while traffic_video.isOpened():
    ret, frame = traffic_video.read()
    # If a frame is not returned, we've reached the end of the video.
    if not ret:
        break
    
    # Run the YOLO model on the current frame to detect objects.
    results = yolo_model(frame)
    detected_objects = []
    
    # Process each detection from the YOLO model.
    for result in results:
        for box in result.boxes.data:
            # Unpack the bounding box coordinates, confidence, and class ID.
            x1, y1, x2, y2, conf, class_id = box
            class_id = int(class_id.item())
            
            # Process only if the detected object is one we are interested in.
            if class_id in object_classes:
                object_name = object_classes[class_id]
                detected_objects.append(object_name)
                
                # Create a label with the object name and detection confidence.
                label = f"{object_name} ({conf:.2f})"
                color = colors.get(object_name, (255, 255, 255))  # Defaults to white if not found
                
                # Draw the bounding box and label on the frame.
                cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), color, 2)
                cv2.putText(frame, label, (int(x1), int(y1) - 5), 
                            cv2.FONT_HERSHEY_SIMPLEX, label_font_scale, color, label_thickness)
    
    # ---------------------------------------------------------------------------------
    # Determine traffic congestion by counting vehicle objects (excluding pedestrians and cyclists).
    vehicle_count = sum(1 for obj in detected_objects if obj in ["car", "motorbike", "bus", "truck", "emergency_vehicle"])
    
    if vehicle_count > congestion_threshold:
        light_status = "Congestion Detected"
        light_color = (0, 0, 255)  # Red in BGR
    else:
        light_status = "Normal Flow"
        light_color = (0, 255, 0)  # Green in BGR
    
    # Display the traffic status on the frame with larger text.
    cv2.putText(frame, light_status, (50, 50), cv2.FONT_HERSHEY_SIMPLEX, status_font_scale, light_color, status_thickness)
    
    # ---------------------------------------------------------------------------------
    # Create a legend in the corner showing the count of each detected object type.
    counts = Counter(detected_objects)
    key_start_x = 10
    key_start_y = 70
    key_line_height = 30  # Vertical spacing between legend entries

    for idx, (obj_name, count) in enumerate(counts.items()):
        # Draw a small colored rectangle as the legend color patch.
        cv2.rectangle(frame, 
                      (key_start_x, key_start_y + idx * key_line_height), 
                      (key_start_x + 20, key_start_y + 20 + idx * key_line_height), 
                      colors.get(obj_name, (255, 255, 255)), 
                      -1)
        # Display the object name and count next to the color patch with larger text.
        cv2.putText(frame, f"{obj_name}: {count}", 
                    (key_start_x + 30, key_start_y + 15 + idx * key_line_height), 
                    cv2.FONT_HERSHEY_SIMPLEX, legend_font_scale, (255, 255, 255), legend_thickness)
    
    # ---------------------------------------------------------------------------------
    # Display the frame with all the drawn overlays.
    cv2.imshow("Traffic AI", frame)
    # Press 'q' to quit the video processing loop.
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release video resources and close all OpenCV windows.
traffic_video.release()
cv2.destroyAllWindows()
