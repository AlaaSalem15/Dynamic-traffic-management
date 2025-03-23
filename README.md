# Dynamic-traffic-management
This repository contains three Python projects that together explore different aspects of traffic analysis and simulation. One project uses advanced object detection on real traffic footage, while the other two simulate traffic flow at an intersection using Pygame.

before continuing, unzip the images file and download all the files in the same folder, aswell as download a video showing traffic congestion from youtube to test the image recognition software.
Prerequisites:

Ensure you have Python 3.8+ installed. You will also need to install the following Python packages:

**opencv-python**

**numpy**

  **torch**
  
  **ultralytics**
  
  **pygame**

# image_recognition.py:
Uses the YOLOv8 model (via the ultralytics package) and OpenCV to perform real-time object detection on traffic video footage.
Detects traffic-related objects such as cars, motorbikes, buses, trucks, and emergency vehicles.
Draws bounding boxes with labels and displays a legend showing counts of each detected object.
Determines traffic congestion by comparing the number of vehicles to a defined threshold and then displays a status message ("Congestion Detected" or "Normal Flow").

configurable variables:
- video used, download your own video as one is not provided
- congestion threshold
- Object classes, object types


#Dynamic_sim.py:
Simulates traffic flow at an intersection using Pygame and a backbone of another github repo. Vehicles (cars, buses, trucks, bikes, and ambulances) are spawned randomly based on weighted probabilities. Vehicles move across the intersection according to traffic signal timings. The simulation includes a traffic light state machine that cycles through green, yellow, and red, using configurable timer values. The program also keeps track of throughput statistics (e.g., the total number of vehicles that have passed) and displays them on-screen.

Configurable variables:
- Traffic Signal Timers: DEFAULT_GREEN_TIME, DEFAULT_YELLOW_TIME, and DEFAULT_RED determine the duration of green, yellow, and red phases.
- Vehicle Speeds: Speeds for each vehicle type (all set to 3 by default) can be adjusted.
- Vehicle Spawn Settings: vehicleTypes and vehicleWeights control which vehicles appear and how frequently (ambulances are less common currently).

#Static_sim.py:
Does the exact same purpose as above, but rather than rely on the traffic density of each lane to autonomously change traffic lights, it relies on an ordinary timed system like most traffic lights, also counts vehicles crossing a boundary (in this case the stopping line rather than edge of the frame) and provides a timer and vehicles per minute counter for comparitive purposes, the exact same variables are configurable as above.

mentions:
the backbone of static_sim.py and dynamic_sim.py uses code for the pygame from this repo: https://github.com/mihir-m-gandhi/Basic-Traffic-Intersection-Simulation

this code was made for HTG 2025 London.

sincerely,
Alaa Salem



