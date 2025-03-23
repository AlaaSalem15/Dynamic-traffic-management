import random
import time
import threading
import pygame
import sys

# CONFIG: All necessary variables
# --------------------------------------------------------------
# Global counter for vehicles that have passed.
vehiclesPassedCounter = 0

def Main():
    global vehiclesPassedCounter  # Allows modification inside methods/classes.

    # Default values of signal timers.
    defaultGreen = {0: 10, 1: 10, 2: 10, 3: 10}
    defaultRed = 150
    defaultYellow = 5

    signals = []
    noOfSignals = 4
    currentGreen = 0
    nextGreen = (currentGreen + 1) % noOfSignals
    currentYellow = 0
    speeds = {'car': 3,
              'bus': 3,
              'truck': 3,
              'bike': 3}  # All vehicles have the same speed in this test; adjust as needed.

    # No ambulances in this playtest; hence, no weighting is necessary.
    x = {'right': [0, 0, 0], 'down': [755, 727, 697], 'left': [1400, 1400, 1400], 'up': [602, 627, 657]}
    y = {'right': [348, 370, 398], 'down': [0, 0, 0], 'left': [498, 466, 436], 'up': [800, 800, 800]}
    vehicles = {
        'right': {0: [], 1: [], 2: [], 'crossed': 0},
        'down': {0: [], 1: [], 2: [], 'crossed': 0},
        'left': {0: [], 1: [], 2: [], 'crossed': 0},
        'up': {0: [], 1: [], 2: [], 'crossed': 0}
    }
    vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike'}
    directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

    signalCoods = [(530, 230), (810, 230), (810, 570), (530, 570)]
    signalTimerCoods = [(530, 210), (810, 210), (810, 550), (530, 550)]

    stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
    defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}
    stoppingGap = 15
    movingGap = 15

    # PYGAME SETUP
    # --------------------------------------------------------------
    pygame.init()
    simulation = pygame.sprite.Group()

    # CLASS DEFINITIONS
    # --------------------------------------------------------------
    class TrafficSignal:
        def __init__(self, red, yellow, green):
            self.red = red
            self.yellow = yellow
            self.green = green
            self.signalText = ""

    class Vehicle(pygame.sprite.Sprite):
        def __init__(self, lane, vehicleClass, direction_number, direction):
            pygame.sprite.Sprite.__init__(self)
            self.lane = lane
            self.vehicleClass = vehicleClass
            self.speed = speeds[vehicleClass]
            self.direction_number = direction_number
            self.direction = direction
            self.x = x[direction][lane]
            self.y = y[direction][lane]
            self.crossed = 0  # Indicates if the vehicle has passed the stop line.
            vehicles[direction][lane].append(self)
            self.index = len(vehicles[direction][lane]) - 1
            path = "images/" + direction + "/" + vehicleClass + ".png"
            self.image = pygame.image.load(path)

            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index - 1].crossed == 0:
                if direction == 'right':
                    self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].image.get_rect().width - stoppingGap
                elif direction == 'left':
                    self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].image.get_rect().width + stoppingGap
                elif direction == 'down':
                    self.stop = vehicles[direction][lane][self.index - 1].stop - vehicles[direction][lane][self.index - 1].image.get_rect().height - stoppingGap
                elif direction == 'up':
                    self.stop = vehicles[direction][lane][self.index - 1].stop + vehicles[direction][lane][self.index - 1].image.get_rect().height + movingGap
            else:
                self.stop = defaultStop[direction]

            if direction == 'right':
                temp = self.image.get_rect().width + stoppingGap
                x[direction][lane] -= temp
            elif direction == 'left':
                temp = self.image.get_rect().width + stoppingGap
                x[direction][lane] += temp
            elif direction == 'down':
                temp = self.image.get_rect().height + stoppingGap
                y[direction][lane] -= temp
            elif direction == 'up':
                temp = self.image.get_rect().height + stoppingGap
                y[direction][lane] += temp
            simulation.add(self)

        def render(self, screen):
            screen.blit(self.image, (self.x, self.y))

        def move(self):
            global vehiclesPassedCounter  # Update the global counter when a vehicle passes.
            nonlocal currentGreen, currentYellow
            # For each direction, check if the vehicle has crossed its stop line.
            if self.direction == 'right':
                if self.crossed == 0 and self.x + self.image.get_rect().width > stopLines[self.direction]:
                    self.crossed = 1
                    vehiclesPassedCounter += 1
                if ((self.x + self.image.get_rect().width <= self.stop or self.crossed == 1 or (currentGreen == 0 and currentYellow == 0))
                    and (self.index == 0 or self.x + self.image.get_rect().width < (vehicles[self.direction][self.lane][self.index - 1].x - movingGap))):
                    self.x += self.speed
            elif self.direction == 'down':
                if self.crossed == 0 and self.y + self.image.get_rect().height > stopLines[self.direction]:
                    self.crossed = 1
                    vehiclesPassedCounter += 1
                if ((self.y + self.image.get_rect().height <= self.stop or self.crossed == 1 or (currentGreen == 1 and currentYellow == 0))
                    and (self.index == 0 or self.y + self.image.get_rect().height < (vehicles[self.direction][self.lane][self.index - 1].y - movingGap))):
                    self.y += self.speed
            elif self.direction == 'left':
                if self.crossed == 0 and self.x < stopLines[self.direction]:
                    self.crossed = 1
                    vehiclesPassedCounter += 1
                if ((self.x >= self.stop or self.crossed == 1 or (currentGreen == 2 and currentYellow == 0))
                    and (self.index == 0 or self.x > (vehicles[self.direction][self.lane][self.index - 1].x + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().width + movingGap))):
                    self.x -= self.speed
            elif self.direction == 'up':
                if self.crossed == 0 and self.y < stopLines[self.direction]:
                    self.crossed = 1
                    vehiclesPassedCounter += 1
                if ((self.y >= self.stop or self.crossed == 1 or (currentGreen == 3 and currentYellow == 0))
                    and (self.index == 0 or self.y > (vehicles[self.direction][self.lane][self.index - 1].y + vehicles[self.direction][self.lane][self.index - 1].image.get_rect().height + movingGap))):
                    self.y -= self.speed

    def initialize():
        ts1 = TrafficSignal(0, defaultYellow, defaultGreen[0])
        signals.append(ts1)
        ts2 = TrafficSignal(ts1.red + ts1.yellow + ts1.green, defaultYellow, defaultGreen[1])
        signals.append(ts2)
        ts3 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[2])
        signals.append(ts3)
        ts4 = TrafficSignal(defaultRed, defaultYellow, defaultGreen[3])
        signals.append(ts4)

    def generateVehicles():
        while True:
            vehicle_type = random.randint(0, 3)
            lane_number = random.randint(1, 2)
            temp = random.randint(0, 99)
            direction_number = 0
            dist = [25, 50, 75, 100]
            if temp < dist[0]:
                direction_number = 0
            elif temp < dist[1]:
                direction_number = 1
            elif temp < dist[2]:
                direction_number = 2
            elif temp < dist[3]:
                direction_number = 3
            Vehicle(lane_number, vehicleTypes[vehicle_type], direction_number, directionNumbers[direction_number])
            time.sleep(1)

    initialize()
    last_update_time = time.time()

    # Simulation start time for the timer.
    start_time = time.time()

    black = (0, 0, 0)
    white = (255, 255, 255)

    screenWidth = 1400
    screenHeight = 800
    screenSize = (screenWidth, screenHeight)
#all image features from github repo
    background = pygame.image.load('images/intersection.png')
    screen = pygame.display.set_mode(screenSize)
    pygame.display.set_caption("SIMULATION")
    redSignal = pygame.image.load('images/signals/red.png')
    yellowSignal = pygame.image.load('images/signals/yellow.png')
    greenSignal = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)

    thread2 = threading.Thread(name="generateVehicles", target=generateVehicles)
    thread2.daemon = True
    thread2.start()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()

        screen.blit(background, (0, 0))
        for i in range(0, noOfSignals):
            if i == currentGreen:
                if currentYellow == 1:
                    signals[i].signalText = signals[i].yellow
                    screen.blit(yellowSignal, signalCoods[i])
                else:
                    signals[i].signalText = signals[i].green
                    screen.blit(greenSignal, signalCoods[i])
            else:
                if signals[i].red <= 10:
                    signals[i].signalText = signals[i].red
                else:
                    signals[i].signalText = "---"
                screen.blit(redSignal, signalCoods[i])
        signalTexts = ["", "", "", ""]
        for i in range(0, noOfSignals):
            signalTexts[i] = font.render(str(signals[i].signalText), True, white, black)
            screen.blit(signalTexts[i], signalTimerCoods[i])
        for vehicle in simulation:
            screen.blit(vehicle.image, [vehicle.x, vehicle.y])
            vehicle.move()

        current_time = time.time()
        if current_time - last_update_time >= 1:
            last_update_time = current_time
            if signals[currentGreen].green > 0:
                signals[currentGreen].green -= 1
            elif signals[currentGreen].yellow > 0:
                currentYellow = 1
                signals[currentGreen].yellow -= 1
                for i in range(0, 3):
                    for vehicle in vehicles[directionNumbers[currentGreen]][i]:
                        vehicle.stop = defaultStop[directionNumbers[currentGreen]]
            else:
                currentYellow = 0
                signals[currentGreen].green = defaultGreen[currentGreen]
                signals[currentGreen].yellow = defaultYellow
                signals[currentGreen].red = defaultRed
                currentGreen = nextGreen
                nextGreen = (currentGreen + 1) % noOfSignals
                signals[nextGreen].red = signals[currentGreen].yellow + signals[currentGreen].green

        # Compute simulation timer and vehicles per minute.
        elapsed_time = time.time() - start_time
        simulationTime = int(elapsed_time)
        vehiclesPerMinute = vehiclesPassedCounter / (elapsed_time / 60) if elapsed_time > 0 else 0

        # Render the timer and vehicle counters on screen.
        timer_text = font.render("Time: " + str(simulationTime) + " sec", True, white, black)
        passed_text = font.render("Vehicles Passed: " + str(vehiclesPassedCounter), True, white, black)
        vpm_text = font.render("Vehicles/Min: " + str(int(vehiclesPerMinute)), True, white, black)
        screen.blit(timer_text, (10, 10))
        screen.blit(passed_text, (10, 40))
        screen.blit(vpm_text, (10, 70))

        pygame.display.update()

if __name__ == "__main__":
    Main()
