import airsim
import win32gui
import keyboard
import math
import numpy
import time

"""
Look on the left or right edge of the screen to turn the camera, look bottom left to move down and bottom right to move up; fixate on a point for at least 2 seconds to have the drone go there.
There is momentum with the fixating action (if you fixate multiple times without turning the camera or moving up/down you will go further).
"""

# parameters used to detemine the threshold when mapping to cardinal directions
X_RESOLUTION = 1920
Y_RESOLUTION = 1080
MARGIN = 0.1

leftbound = MARGIN * X_RESOLUTION
rightbound = (1 - MARGIN) * X_RESOLUTION
upbound = MARGIN * Y_RESOLUTION
downbound = (1 - MARGIN) * Y_RESOLUTION

# connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

client.takeoffAsync().join()

base_speed = 10
rotate_deg = 22.5

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
        0: "Rotate Right",
        1: "Rotate Left",
        2: "Move Forward",
        3: "Move Up",
        4: "Move Down"
    }

    print(switcher.get(prev_dir, "Invalid"), " ", increment)


def main():
    print("Setup Complete")
    
    # to help with momentum
    prev_dir = -1
    prev_cnt = 0

    # to help with detecting gaze fixation
    x_old = 0
    y_old = 0

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
        increment = rotate_deg

        gaze_pos = win32gui.GetCursorPos()
        x = gaze_pos[0]
        y = gaze_pos[1]

        # look right to rotate right
        if (x > rightbound and (upbound <= y <= downbound)):
            _, prev_dir, prev_cnt = calculate_increment(0, prev_dir, prev_cnt)
            client.rotateByYawRateAsync(increment, 1).join()
            renormalize(x_start, y_start)   # normalize x and y position after doing a rotation, otherwise it drifts
        
        # look left to rotate left
        elif (x < leftbound and (upbound <= y <= downbound)):
            _, prev_dir, prev_cnt = calculate_increment(1, prev_dir, prev_cnt)
            client.rotateByYawRateAsync(-increment, 1).join()
            renormalize(x_start, y_start)

        # look bottom-right to move up
        elif (y > upbound and x > rightbound):
            increment, prev_dir, prev_cnt = calculate_increment(2, prev_dir, prev_cnt)
            z_start = z_start - increment
            client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()

        # look bottom-left to move down
        elif (y > upbound and x < leftbound):
            increment, prev_dir, prev_cnt = calculate_increment(3, prev_dir, prev_cnt)
            z_start = z_start + increment
            client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()
        
        else:
            # if two polling points in a row are close, move towards that gaze point
            if (x > x_old - 100) and (x < x_old + 100) and (y > y_old - 100) and (y < y_old + 100):
                increment, prev_dir, prev_cnt = calculate_increment(4, prev_dir, prev_cnt)

                # convert pixel value into radians then degrees
                theta = (x - X_RESOLUTION / 2) * 3 / 64 / 180 * math.pi
                rho = (y - Y_RESOLUTION / 2) * 3 / 64 / 180 * math.pi

                # find the drone/camera orientation
                orientation = client.getMultirotorState().kinematics_estimated.orientation
                
                # combine the orientation of the camera with the horizontal offset (based on gaze) to determine xy-plane vector
                # weird math because of homogenous coordinatates
                if (orientation.w_val > 0):
                    sign = 1
                    theta = math.acos(orientation.z_val) * 2 - theta
                else: 
                    sign = -1
                    theta = math.acos(orientation.z_val) * 2 + theta
                
                if (theta > 2 * math.pi):
                    theta = 2 * math.pi - (theta - 2 * math.pi)
                    sign = -sign
                elif (theta < 0):
                    theta = -theta
                    sign = -sign
                
                x_start -= math.cos(theta) * increment
                
                if (sign > 0):
                    y_start += math.sin(theta) * increment
                else:
                    y_start -= math.sin(theta) * increment
                
                # offset based on the height on the monitor you look at
                z_start += math.sin (rho) * increment

                client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()
                # rotate left and right to speed up camera stablization                
                client.rotateByYawRateAsync(-5, 1).join()
                client.rotateByYawRateAsync(5, 1).join()

                # reset buffer
                x_old = 0
                y_old = 0

            else:
                x_old = x
                y_old = y

            # time to wait before polling again
            time.sleep(1)
        
        print_command(prev_dir, increment)
        
main()