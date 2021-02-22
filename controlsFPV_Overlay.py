

# Can play around with these values to change the size and location of circles for UI, the hitboxes in the logic also use these variables
RADIUS = 100
BUTTON_OFFSET = 200
# Can play around with these variables to figure out hold long you have to be within a circle to trigger an action (more-or-less, THRESHOLD * INTERVAL)
FIXATION_THRESHOLD = 5
POLLING_INTERVAL = 0.3


################# OVERLAY #######################

import sys
import threading

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

showGuides = True
showDescriptions = True

class CustomWindow(QMainWindow):
    def __init__(self):
        super().__init__()

    def paintEvent(self, event=None):
        painter = QPainter(self)
        
        if showGuides:
            painter.setOpacity(0.4)
            painter.setPen(QPen(Qt.black, 5, Qt.SolidLine))
            painter.setBrush(QBrush(Qt.red, Qt.SolidPattern))

            centerPoint = QDesktopWidget().availableGeometry(0).center()
            print(centerPoint.x(), centerPoint.y())
            painter.drawEllipse(centerPoint, RADIUS, RADIUS)
            painter.drawEllipse(centerPoint - QPoint(BUTTON_OFFSET, 0), RADIUS, RADIUS)
            painter.drawEllipse(centerPoint + QPoint(BUTTON_OFFSET, 0), RADIUS, RADIUS)
            painter.drawEllipse(centerPoint - QPoint(0, BUTTON_OFFSET), RADIUS, RADIUS)
            painter.drawEllipse(centerPoint + QPoint(0, BUTTON_OFFSET), RADIUS, RADIUS)
        
            if showDescriptions:
                centerPoint = QDesktopWidget().availableGeometry(0).center()

                painter.setOpacity(1)
                painter.drawText(centerPoint.x() - 20, centerPoint.y(), "Forward")
                painter.drawText(centerPoint.x() - BUTTON_OFFSET - 15, centerPoint.y(), "R.Left")
                painter.drawText(centerPoint.x() + BUTTON_OFFSET - 15, centerPoint.y(), "R.Right")
                painter.drawText(centerPoint.x() - 5, centerPoint.y() - BUTTON_OFFSET, "Up")
                painter.drawText(centerPoint.x() - 10, centerPoint.y() + BUTTON_OFFSET, "Down")


def toggleButtonClicked():
    global showGuides
    showGuides = not showGuides 
    toggleButton.setText("Show Guide Points" if not showGuides else "Hide Guide Points")

def descriptionButtonClicked():
    global showDescriptions
    showDescriptions = not showDescriptions 
    descriptionButton.setText("Show Descriptions" if not showDescriptions else "Hide Descriptions")

def start(apps):
    apps.exec_()

app = QApplication(sys.argv)

# Create the main window
window = CustomWindow()
window.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint) # so its borderless and stays on top
window.setAttribute(Qt.WA_NoSystemBackground, True)
window.setAttribute(Qt.WA_TranslucentBackground, True)

# Create the toggle button
toggleButton = QPushButton(window)
toggleButton.setGeometry(QRect(240, 190, 120, 31))
toggleButton.setText("Hide Guide Points")
toggleButton.clicked.connect(toggleButtonClicked)

qr = toggleButton.frameGeometry() # in right button
cp = QDesktopWidget().availableGeometry(0).topRight()
qr.moveTopRight(cp)
toggleButton.move(qr.topLeft())

# Create the description button
descriptionButton = QPushButton(window)
descriptionButton.setGeometry(QRect(240, 190, 120, 31))
descriptionButton.setText("Hide Descriptions")
descriptionButton.clicked.connect(descriptionButtonClicked)

describeQr = descriptionButton.frameGeometry() # in the top right
describeCp = QDesktopWidget().availableGeometry(0).topRight() + QPoint(0, 50)
describeQr.moveTopRight(describeCp)
descriptionButton.move(describeQr.topLeft())

# Create the Quit button 
quitButton = QPushButton(window)
quitButton.setGeometry(QRect(240, 190, 120, 31))
quitButton.setText("Quit")
quitButton.clicked.connect(app.quit)

quitQr = quitButton.frameGeometry() # in the top left
quitCp = QDesktopWidget().availableGeometry(0).topLeft()
quitQr.moveTopLeft(quitCp)
quitButton.move(quitQr.topLeft())


################# Control Scheme #######################

import airsim
import win32gui
import win32api 
import keyboard
import math
import enum
import time

# parameters used to detemine the threshold when mapping to cardinal directions
width = win32api.GetSystemMetrics(0)
height = win32api.GetSystemMetrics(1) * 0.963 # GUI size doesn't cover the whole screen due to taskbar (I think)


print(width, height)
# connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

client.takeoffAsync().join()

base_speed = 8
rotate = 22.5

def calculate_increment(caller, prev_dir, prev_cnt):
    # update momentum variables
    if caller != prev_dir:
        prev_dir = caller
        prev_cnt = 0
    elif caller >= 2:
        prev_cnt += 1
    
    # calculate position increment based on momemtum
    return base_speed * 1.5 ** prev_cnt, prev_dir, prev_cnt


def renormalize(x_start, y_start):
    position = client.getMultirotorState().kinematics_estimated.position
    z_start = position.z_val
    client.moveToPositionAsync(x_start, y_start, z_start, base_speed, 5).join()

def print_command(prev_dir, increment):
    switcher = {
        1: "Rotate Left",
        2: "Rotate Right",
        3: "Move Down",
        4: "Move Up",
        5: "Move Straight"
    }

    print(switcher.get(prev_dir, "Invalid"), " ", increment)

class Button(enum.Enum):
    Other = 0
    Left = 1
    Right = 2
    Down = 3
    Up = 4
    Center = 5

def main():
    print("Setup Complete")

    # to help with momentum
    prev_dir = -1
    prev_cnt = 0

    # to help with detecting gaze fixation
    prev_circle = 0
    curr_circle = 0
    same_circle_count = 0

    while(1):
        # if key is pressed stop giving inputs until key C is pressed
        # Note: key S has to be pressed (held down) until the current action has completed (this won't trigger while drone is moving)
        if keyboard.is_pressed('s'):
                while not keyboard.is_pressed('c'):
                    continue
                
        position = client.getMultirotorState().kinematics_estimated.position
        x_start = position.x_val
        y_start = position.y_val 
        z_start = position.z_val
        increment = rotate

        gaze_pos = win32gui.GetCursorPos()
        x = gaze_pos[0]
        y = gaze_pos[1]

        # Find position of current point
        if math.sqrt((y - height / 2) ** 2 + (x - (width / 2 - BUTTON_OFFSET)) ** 2) < RADIUS:
            curr_circle = Button.Left
        elif math.sqrt((y - height / 2) ** 2 + (x - (width / 2 + BUTTON_OFFSET)) ** 2) < RADIUS:
            curr_circle = Button.Right 
        elif math.sqrt((y - (height / 2 + BUTTON_OFFSET)) ** 2 + (x - width / 2) ** 2) < RADIUS:
            curr_circle = Button.Down
        elif math.sqrt((y - (height / 2 - BUTTON_OFFSET)) ** 2 + (x - width / 2) ** 2) < RADIUS:
            curr_circle = Button.Up
        elif math.sqrt((y - height / 2) ** 2 + (x - width / 2) ** 2) < RADIUS:
            curr_circle = Button.Center
        else:
            curr_circle = Button.Other

        # Update counter tracking fixation
        if prev_circle == curr_circle:
            same_circle_count += 1
        else:
            same_circle_count = 0
        
        # If same circle was polled enough times in a row
        if same_circle_count >= FIXATION_THRESHOLD:
            # LEFT
            if prev_circle == Button.Left and curr_circle == Button.Left:
                _, prev_dir, prev_cnt = calculate_increment(1, prev_dir, prev_cnt)
                client.rotateByYawRateAsync(-increment, 1).join()
                renormalize(x_start, y_start) # normalize x and y position after doing a rotation, otherwise it drifts
            # RIGHT
            elif prev_circle == Button.Right and  curr_circle == Button.Right:
                _, prev_dir, prev_cnt = calculate_increment(2, prev_dir, prev_cnt)
                client.rotateByYawRateAsync(increment, 1).join()
                renormalize(x_start, y_start)
            # DOWN
            elif prev_circle == Button.Down and curr_circle == Button.Down:
                increment, prev_dir, prev_cnt = calculate_increment(3, prev_dir, prev_cnt)
                z_start = z_start + increment
                client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()
            # UP
            elif prev_circle == Button.Up and curr_circle == Button.Up:
                increment, prev_dir, prev_cnt = calculate_increment(4, prev_dir, prev_cnt)
                z_start = z_start - increment
                client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()
            # CENTER
            elif prev_circle == Button.Center and curr_circle == Button.Center:            
                increment, prev_dir, prev_cnt = calculate_increment(5, prev_dir, prev_cnt)
                orientation = client.getMultirotorState().kinematics_estimated.orientation

                theta = math.acos(orientation.z_val) * 2
                x_start -= math.cos(theta) * increment
                if (orientation.w_val > 0):
                    y_start += math.sin(theta) * increment
                else:
                    y_start -= math.sin(theta) * increment

                client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()           
            
        else: 
            prev_circle = curr_circle
            time.sleep(POLLING_INTERVAL)
            continue
        
        # If instruction happened, reset buffer and print instruction
        prev_circle = Button.Other
        same_circle_count = 0
        print_command(prev_dir, increment)


# Run the application
threading.Thread(target=main).start() # Control scheme starts in other thread
window.showFullScreen()
sys.exit(app.exec_()) # QGui must run in the main thread
