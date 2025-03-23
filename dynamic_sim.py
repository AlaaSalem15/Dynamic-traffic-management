import random
import time
import threading
import pygame
import sys

def SmartMain():
    # CONFIG: all nessessary variables
    # --------------------------------------------------------------
    DEFAULT_GREEN_TIME  = 6    # seconds of green (alter based on road type, traffic, etc)
    DEFAULT_YELLOW_TIME = 3    # seconds of yellow
    DEFAULT_RED         = 150  # for signal initialization

    defaultGreen  = {0: DEFAULT_GREEN_TIME, 1: DEFAULT_GREEN_TIME, 2: DEFAULT_GREEN_TIME, 3: DEFAULT_GREEN_TIME}
    defaultYellow = DEFAULT_YELLOW_TIME
    defaultRed    = DEFAULT_RED

    speeds = {
        'car':       3,
        'bus':       3,
        'truck':     3,
        'bike':      3,
        'ambulance': 3
    } #all vehicles at the same speed in this test, you can change it based on the need

    # Use weighted selection for vehicles, alter to playtest, makes ambulances more rare since we arent in covid any longer :)
    vehicleTypes = {0: 'car', 1: 'bus', 2: 'truck', 3: 'bike', 4: 'ambulance'}
    vehicleWeights = [40, 20, 20, 15, 1]
#road limitations based on the intersection image from the github repo used
    x = {
        'right': [0, 0, 0],
        'down':  [755, 727, 697],
        'left':  [1400, 1400, 1400],
        'up':    [602, 627, 657]
    }
    y = {
        'right': [348, 370, 398],
        'down':  [0, 0, 0],
        'left':  [498, 466, 436],
        'up':    [800, 800, 800]
    }
    stopLines = {'right': 590, 'down': 330, 'left': 800, 'up': 535}
    defaultStop = {'right': 580, 'down': 320, 'left': 810, 'up': 545}

    stoppingGap = 15
    movingGap   = 15

    vehicles = {
        'right': {0: [], 1: [], 2: [], 'crossed': 0},
        'down':  {0: [], 1: [], 2: [], 'crossed': 0},
        'left':  {0: [], 1: [], 2: [], 'crossed': 0},
        'up':    {0: [], 1: [], 2: [], 'crossed': 0}
    }
    directionNumbers = {0: 'right', 1: 'down', 2: 'left', 3: 'up'}

    # Traffic light state machine variables
    currentDirection = 0      # which direction is currently green
    currentState = 'GREEN'      # either 'GREEN' or 'YELLOW'
    timeLeft = DEFAULT_GREEN_TIME

    # Throughput statistics, resets all timers for the test
    simulationStart = time.time()
    passedVehicles = 0

    # PYGAME SETUP
    # --------------------------------------------------------------
    pygame.init()
    screenWidth, screenHeight = 1400, 800
    screen = pygame.display.set_mode((screenWidth, screenHeight))
    pygame.display.set_caption("Dynamic traffic Simulation")
    background = pygame.image.load('images/intersection.png')
    redSignalImg = pygame.image.load('images/signals/red.png')
    yellowSignalImg = pygame.image.load('images/signals/yellow.png')
    greenSignalImg = pygame.image.load('images/signals/green.png')
    font = pygame.font.Font(None, 30)
    black = (0,0,0)
    white = (255,255,255)
    signalCoods = [(530,230), (810,230), (810,570), (530,570)]
    signalTimerCoods = [(530,210), (810,210), (810,550), (530,550)]
    simulationGroup = pygame.sprite.Group()

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
            self.crossed = 0  # 0: not yet crossed; 1: crossed

            # Stamp spawn time for wait-time priority
            self.spawn_time = time.time()

            vehicles[direction][lane].append(self)
            self.index = len(vehicles[direction][lane]) - 1

            path = "images/" + direction + "/" + vehicleClass + ".png"
            self.image = pygame.image.load(path)

            if len(vehicles[direction][lane]) > 1 and vehicles[direction][lane][self.index-1].crossed == 0:
                prev = vehicles[direction][lane][self.index-1]
                if direction == 'right':
                    self.stop = prev.stop - prev.image.get_width() - stoppingGap
                elif direction == 'left':
                    self.stop = prev.stop + prev.image.get_width() + stoppingGap
                elif direction == 'down':
                    self.stop = prev.stop - prev.image.get_height() - stoppingGap
                elif direction == 'up':
                    self.stop = prev.stop + prev.image.get_height() + stoppingGap
            else:
                self.stop = defaultStop[direction]

            if direction == 'right':
                temp = self.image.get_width() + stoppingGap
                x[direction][lane] -= temp
            elif direction == 'left':
                temp = self.image.get_width() + stoppingGap
                x[direction][lane] += temp
            elif direction == 'down':
                temp = self.image.get_height() + stoppingGap
                y[direction][lane] -= temp
            elif direction == 'up':
                temp = self.image.get_height() + stoppingGap
                y[direction][lane] += temp
            simulationGroup.add(self)

        def render(self, surface):
            surface.blit(self.image, (self.x, self.y))

        def move(self):
            nonlocal currentDirection, currentState
            tol = 5  # collision tolerance in pixels
            d = self.direction
            w = self.image.get_width()
            h = self.image.get_height()

            # Recalculate index in lane to avoid stale values after removals
            lane_list = vehicles[d][self.lane]
            if self in lane_list:
                self.index = lane_list.index(self)
            else:
                self.index = 0

            # Mark as crossed if front edge reaches or passes the stop line
            if self.crossed == 0:
                if (d == 'right' and (self.x + w >= stopLines[d])) or \
                   (d == 'down' and (self.y + h >= stopLines[d])) or \
                   (d == 'left' and (self.x <= stopLines[d])) or \
                   (d == 'up' and (self.y <= stopLines[d])):
                    self.crossed = 1

            shouldMove = False
            if self.crossed:
                shouldMove = True
            else:
                if d == 'right':
                    if (self.x + w < self.stop) or (currentDirection == 0 and currentState == 'GREEN'):
                        shouldMove = True
                elif d == 'down':
                    if (self.y + h < self.stop) or (currentDirection == 1 and currentState == 'GREEN'):
                        shouldMove = True
                elif d == 'left':
                    if (self.x > self.stop) or (currentDirection == 2 and currentState == 'GREEN'):
                        shouldMove = True
                elif d == 'up':
                    if (self.y > self.stop) or (currentDirection == 3 and currentState == 'GREEN'):
                        shouldMove = True

            if not shouldMove:
                return

            # Collision check with vehicle ahead in lane, was used when vehicles had different speeds, kept incase values were altered
            if self.index > 0:
                if self.index - 1 < len(lane_list):
                    frontV = lane_list[self.index - 1]
                    if frontV.crossed == 0:
                        if d == 'right' and (self.x + w + tol < frontV.x - movingGap):
                            self.x += self.speed
                        elif d == 'down' and (self.y + h + tol < frontV.y - movingGap):
                            self.y += self.speed
                        elif d == 'left' and (self.x - tol > frontV.x + frontV.image.get_width() + movingGap):
                            self.x -= self.speed
                        elif d == 'up' and (self.y - tol > frontV.y + frontV.image.get_height() + movingGap):
                            self.y -= self.speed
                    else:
                        if d == 'right':
                            if (self.x + w + tol < frontV.x):
                                self.x += self.speed
                            else:
                                self.x += self.speed * 0.5
                        elif d == 'down':
                            if (self.y + h + tol < frontV.y):
                                self.y += self.speed
                            else:
                                self.y += self.speed * 0.5
                        elif d == 'left':
                            if (self.x - tol > frontV.x + frontV.image.get_width()):
                                self.x -= self.speed
                            else:
                                self.x -= self.speed * 0.5
                        elif d == 'up':
                            if (self.y - tol > frontV.y + frontV.image.get_height()):
                                self.y -= self.speed
                            else:
                                self.y -= self.speed * 0.5
            else:
                if d == 'right':
                    self.x += self.speed
                elif d == 'down':
                    self.y += self.speed
                elif d == 'left':
                    self.x -= self.speed
                elif d == 'up':
                    self.y -= self.speed

    # --------------------------------------------------------------
    # WAIT-TIME PRIORITY: Compute a lane metric (count + total_wait/scale)
    # --------------------------------------------------------------
    WAIT_SCALE = 2.0
    def getLaneMetric(dIndex):
        dName = directionNumbers[dIndex]
        count = 0
        total_wait = 0
        current_time = time.time()
        for lane in [0, 1, 2]:
            for v in vehicles[dName][lane]:
                if v.crossed == 0:
                    count += 1
                    total_wait += (current_time - v.spawn_time)
        return count + (total_wait / WAIT_SCALE)

    def pickNextDirection():
        # Ambulance priority
        for dIndex in range(4):
            dName = directionNumbers[dIndex]
            for lane in [0, 1, 2]:
                for v in vehicles[dName][lane]:
                    if v.vehicleClass == 'ambulance':
                        return dIndex
        best_dir = currentDirection
        best_metric = getLaneMetric(currentDirection)
        for dIndex in range(4):
            if dIndex == currentDirection:
                continue
            metric = getLaneMetric(dIndex)
            if metric > best_metric * 1.5:
                best_metric = metric
                best_dir = dIndex
        return best_dir


    # VEHICLE GENERATION (with ambulances and weighted spawn)
    # --------------------------------------------------------------
    def generateVehicles():
        while True:
            choice = random.choices([0, 1, 2, 3, 4], weights=vehicleWeights, k=1)[0]
            vtype = vehicleTypes[choice]
            lane_number = random.randint(0, 2)
            r = random.randint(0, 99)
            if r < 25:
                dnum = 0
            elif r < 50:
                dnum = 1
            elif r < 75:
                dnum = 2
            else:
                dnum = 3
            Vehicle(lane_number, vtype, dnum, directionNumbers[dnum])
            time.sleep(1)
    genThread = threading.Thread(target=generateVehicles, daemon=True)
    genThread.start()

    # Remove vehicles that have passed the intersection
    # --------------------------------------------------------------
    def removePassedVehicles():
        nonlocal passedVehicles
        to_remove = []
        for v in simulationGroup:
            w = v.image.get_width()
            h = v.image.get_height()
            if v.direction == 'right' and v.x > screenWidth:
                to_remove.append(v)
            elif v.direction == 'left' and (v.x + w) < 0:
                to_remove.append(v)
            elif v.direction == 'down' and v.y > screenHeight:
                to_remove.append(v)
            elif v.direction == 'up' and (v.y + h) < 0:
                to_remove.append(v)
        for v in to_remove:
            passedVehicles += 1
            simulationGroup.remove(v)
            vehicles[v.direction][v.lane].remove(v)

    # SIGNALS: Initialize signals once
    # --------------------------------------------------------------
    signals = [TrafficSignal(0, defaultYellow, defaultGreen[i]) for i in range(4)]


    # MAIN LOOP
    # --------------------------------------------------------------
    lastTimerUpdate = time.time()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        screen.blit(background, (0, 0))
        for v in simulationGroup:
            v.move()
            v.render(screen)
        removePassedVehicles()

        # Display traffic signals
        for i in range(4):
            if i == currentDirection:
                if currentState == 'GREEN':
                    signals[i].signalText = str(timeLeft)
                    screen.blit(greenSignalImg, signalCoods[i])
                else:
                    signals[i].signalText = str(timeLeft)
                    screen.blit(yellowSignalImg, signalCoods[i])
            else:
                signals[i].signalText = "---"
                screen.blit(redSignalImg, signalCoods[i])
        for i in range(4):
            txtSurf = font.render(signals[i].signalText, True, white, black)
            screen.blit(txtSurf, signalTimerCoods[i])

        # Display throughput statistics: Timer, Passed, Per Min.
        elapsed = time.time() - simulationStart
        timerSurf = font.render(f"Time: {int(elapsed)}s", True, white, black)
        screen.blit(timerSurf, (10, 10))
        passedSurf = font.render(f"Passed: {passedVehicles}", True, white, black)
        screen.blit(passedSurf, (10, 30))
        perMin = (passedVehicles / elapsed * 60) if elapsed > 0 else 0
        pmSurf = font.render(f"Per Min: {perMin:.1f}", True, white, black)
        screen.blit(pmSurf, (10, 50))

        now = time.time()
        if now - lastTimerUpdate >= 1:
            lastTimerUpdate = now
            # Only force a green cycle switch if the current lane becomes empty.
            if currentState == 'GREEN' and timeLeft > 0:
                # Get vehicle count in current lane.
                current_count = len(vehicles[directionNumbers[currentDirection]][0]) + \
                                len(vehicles[directionNumbers[currentDirection]][1]) + \
                                len(vehicles[directionNumbers[currentDirection]][2])
                if current_count == 0:
                    timeLeft = 0
            timeLeft -= 1
            if timeLeft < 0:
                timeLeft = 0
            if timeLeft == 0:
                if currentState == 'GREEN':
                    currentState = 'YELLOW'
                    timeLeft = DEFAULT_YELLOW_TIME
                    for lane in range(3):
                        for veh in vehicles[directionNumbers[currentDirection]][lane]:
                            veh.stop = defaultStop[directionNumbers[currentDirection]]
                else:
                    currentState = 'GREEN'
                    currentDirection = pickNextDirection()
                    timeLeft = DEFAULT_GREEN_TIME
            signals[currentDirection].red = signals[currentDirection].yellow + signals[currentDirection].green
        pygame.display.update()

if __name__ == "__main__":
    SmartMain()
