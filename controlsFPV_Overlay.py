################# CONSTANTS #######################

# Can play around with these values to change the size and location of circles for UI, the hitboxes in the logic also use these variables
RADIUS = 100
BUTTON_OFFSET = 200

# Can play around with these variables to figure out hold long you have to be within a circle to trigger an action (more-or-less, THRESHOLD * INTERVAL)
FIXATION_THRESHOLD = 20
POLLING_INTERVAL = 0.05

################## GLOBALS ######################

# used to change color of UI buttons when the drone is executing an instruction
instruction_executing = 0

# used both in logic to detect gaze and in UI to highlight the circle on which the gaze currently lands (if any)
curr_circle = 0

x = 0
y = 0

from enum import Enum
class Mode(Enum):
    LONG_DISTANCE = 0
    NORMAL = 1
    SHORT_DISTANCE = 2

mode = Mode.LONG_DISTANCE

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
            painter.setPen(QPen(Qt.black, 0, Qt.SolidLine))
            centerPoint = QDesktopWidget().availableGeometry(0).center()
            
            # To draw over the cursor, sucks for a few reasons
            """
            - doesn't move when the drone is performing action
            - can't click on things (you end up clicking on the circle rather than whats behind it)
            - the mouse cursor is still visible
            painter.setOpacity(0.8)
            painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
            painter.drawEllipse(QPoint(x,y), RADIUS / 3, RADIUS / 3)
            """

            painter.setOpacity(0.4)
            painter.setBrush(QBrush(Qt.green, Qt.SolidPattern))
            # if the current gaze lands on a button, highlight that button
            if curr_circle == Button.Center:
                painter.drawRoundedRect(centerPoint.x() - RADIUS, centerPoint.y() - RADIUS, RADIUS * 2, RADIUS * 2, 15, 15)
            elif curr_circle == Button.Left:
                painter.drawRoundedRect(centerPoint.x() - RADIUS - BUTTON_OFFSET, centerPoint.y() - RADIUS, RADIUS * 2, RADIUS * 2, 15, 15)
            elif curr_circle == Button.Right:
                painter.drawRoundedRect(centerPoint.x() - RADIUS + BUTTON_OFFSET, centerPoint.y() - RADIUS, RADIUS * 2, RADIUS * 2, 15, 15)
            elif curr_circle == Button.Up:
                painter.drawRoundedRect(centerPoint.x() - RADIUS, centerPoint.y() - RADIUS - BUTTON_OFFSET, RADIUS * 2, RADIUS * 2, 15, 15)
            elif curr_circle == Button.Down: 
                painter.drawRoundedRect(centerPoint.x() - RADIUS, centerPoint.y() - RADIUS + BUTTON_OFFSET, RADIUS * 2, RADIUS * 2, 15, 15)

            # buttons are different colors depending on if an instruction is executing or not
            if instruction_executing:
                painter.setBrush(QBrush(Qt.gray, Qt.SolidPattern))
            else:
                painter.setBrush(QBrush(Qt.blue, Qt.SolidPattern))

            if curr_circle != Button.Center: 
                painter.drawRoundedRect(centerPoint.x() - RADIUS, centerPoint.y() - RADIUS, RADIUS * 2, RADIUS * 2, 15, 15)
            if curr_circle != Button.Left:
                painter.drawRoundedRect(centerPoint.x() - RADIUS - BUTTON_OFFSET, centerPoint.y() - RADIUS, RADIUS * 2, RADIUS * 2, 15, 15)
            if curr_circle != Button.Right:
                painter.drawRoundedRect(centerPoint.x() - RADIUS + BUTTON_OFFSET, centerPoint.y() - RADIUS, RADIUS * 2, RADIUS * 2, 15, 15)
            if curr_circle != Button.Up:
                painter.drawRoundedRect(centerPoint.x() - RADIUS, centerPoint.y() - RADIUS - BUTTON_OFFSET, RADIUS * 2, RADIUS * 2, 15, 15)
            if curr_circle != Button.Down:
                painter.drawRoundedRect(centerPoint.x() - RADIUS, centerPoint.y() - RADIUS + BUTTON_OFFSET, RADIUS * 2, RADIUS * 2, 15, 15)

            # write text in the middle of each button
            if showDescriptions:
                centerPoint = QDesktopWidget().availableGeometry(0).center()

                font = painter.font()
                font.setPointSize(font.pointSize() * 4)
                painter.setFont(font)
                
                centerPoint.setY(centerPoint.y() + 12)

                painter.drawText(centerPoint.x() - 75, centerPoint.y(), "Forward")
                painter.drawText(centerPoint.x() - BUTTON_OFFSET - 60, centerPoint.y(), "R.Left")
                painter.drawText(centerPoint.x() + BUTTON_OFFSET - 65, centerPoint.y(), "R.Right")
                painter.drawText(centerPoint.x() - 25, centerPoint.y() - BUTTON_OFFSET, "Up")
                painter.drawText(centerPoint.x() - 55, centerPoint.y() + BUTTON_OFFSET, "Down")


def toggleButtonClicked():
    global showGuides
    showGuides = not showGuides 
    toggleButton.setText("Show Guide Points" if not showGuides else "Hide Guide Points")
    window.update()

def descriptionButtonClicked():
    global showDescriptions
    showDescriptions = not showDescriptions 
    descriptionButton.setText("Show Descriptions" if not showDescriptions else "Hide Descriptions")
    window.update()

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

# connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

client.takeoffAsync().join()

def calculate_increment(caller, prev_dir, prev_cnt):
    # update momentum variables
    if caller != prev_dir:
        prev_dir = caller
        prev_cnt = 0
    elif caller >= 2:
        prev_cnt += 1
    
    # update UI
    global instruction_executing
    instruction_executing = 1
    window.update()

    base_speed = rotate = 0
    if mode == Mode.NORMAL:
        base_speed = 8
        rotate = 22.5
    elif mode == Mode.SHORT_DISTANCE:
        base_speed = 4
        rotate = 30
    elif mode == Mode.LONG_DISTANCE:
        base_speed = 16
        rotate = 18

    returnValue = 0
    if caller == 1 or caller == 2:
        returnValue = rotate
    else:
        returnValue = base_speed * 1.5 ** prev_cnt
    # calculate position increment based on momemtum
    return returnValue, prev_dir, prev_cnt


def renormalize(x_start, y_start, speed):
    position = client.getMultirotorState().kinematics_estimated.position
    z_start = position.z_val
    client.moveToPositionAsync(x_start, y_start, z_start, speed, 5).join()


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
        increment = 0

        gaze_pos = win32gui.GetCursorPos()

        global x
        global y
        x = gaze_pos[0]
        y = gaze_pos[1]

        global curr_circle

        # Find position of current point
        if width / 2 - 3 * RADIUS < x < width / 2 - RADIUS and height / 2 - RADIUS < y < height / 2 + RADIUS:
            curr_circle = Button.Left
        elif width / 2 + RADIUS < x < width / 2 + 3 * RADIUS and height / 2 - RADIUS < y < height / 2 + RADIUS:
            curr_circle = Button.Right 
        elif width / 2 - RADIUS < x < width / 2 + RADIUS and height / 2 + RADIUS < y < height / 2 + 3 * RADIUS:
            curr_circle = Button.Down
        elif width / 2 - RADIUS < x < width / 2 + RADIUS and height / 2 - 3 * RADIUS < y < height / 2 - RADIUS:
            curr_circle = Button.Up
        elif width / 2 - RADIUS < x < width / 2 + RADIUS and height / 2 - RADIUS < y < height / 2 + RADIUS:
            curr_circle = Button.Center
        else:
            curr_circle = Button.Other

        # Update UI with current selection
        window.update()

        # Update counter tracking fixation
        if prev_circle == curr_circle:
            same_circle_count += 1
        else:
            same_circle_count = 0
        
        # If same circle was polled enough times in a row
        if same_circle_count >= FIXATION_THRESHOLD:
            # LEFT
            if prev_circle == Button.Left and curr_circle == Button.Left:
                increment, prev_dir, prev_cnt = calculate_increment(1, prev_dir, prev_cnt)
                client.rotateByYawRateAsync(-increment, 1).join()
                renormalize(x_start, y_start, increment) # normalize x and y position after doing a rotation, otherwise it drifts
            # RIGHT
            elif prev_circle == Button.Right and  curr_circle == Button.Right:
                increment, prev_dir, prev_cnt = calculate_increment(2, prev_dir, prev_cnt)
                client.rotateByYawRateAsync(increment, 1).join()
                renormalize(x_start, y_start, increment)
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
        
        # update UI
        global instruction_executing
        instruction_executing = 0
        window.update()

        # If instruction happened, reset buffer and print instruction
        prev_circle = Button.Other
        same_circle_count = 0

        if increment > 0:
            print_command(prev_dir, increment)


# Run the application
threading.Thread(target=main).start() # Control scheme starts in other thread
window.showFullScreen()
sys.exit(app.exec_()) # QGui must run in the main thread (TODO: fix program crashing when exit button is pressed)
