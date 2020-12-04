import airsim
import keyboard
import win32gui
import time
import sys
from threading import Thread


# parameters used to detemine the threshold when mapping to cardinal directions
xlength = 1920
ylength = 1080

margin = 0.2

leftbound = margin * xlength
rightbound = (1 - margin) * xlength
upbound = margin * ylength
downbound = (1 - margin) * ylength


# connect to the AirSim simulator
client = airsim.MultirotorClient()
client.confirmConnection()
client.enableApiControl(True)
client.armDisarm(True)

client.takeoffAsync().join()

speed = 5

def calculate_increment(caller, prev_dir, prev_cnt):
    # update momentum variables
    if caller != prev_dir:
        prev_dir = caller
        prev_cnt = 0
    else:
        prev_cnt += 1
    
    # calculate position increment based on momemtum
    return speed * 1.5 ** prev_cnt, prev_dir, prev_cnt


def main():
    prev_dir = -1
    prev_cnt = 0
    x_start = y_start = z_start = 0

    while(1):
        gaze_pos = win32gui.GetCursorPos()
        x = gaze_pos[0]
        y = gaze_pos[1]

        if (x > rightbound and (upbound <= y <= downbound)):
            increment, prev_dir, prev_cnt = calculate_increment(0, prev_dir, prev_cnt)
            print("RIGHT ", increment)
            y_start = y_start + increment
          
        elif (x < leftbound and (upbound <= y <= downbound)):
            increment, prev_dir, prev_cnt = calculate_increment(1, prev_dir, prev_cnt)
            print("LEFT ", increment)
            y_start = y_start - increment

        elif (y > downbound and (leftbound <= x <= rightbound)):
            increment, prev_dir, prev_cnt = calculate_increment(2, prev_dir, prev_cnt)
            print("BACKWARD ", increment)
            x_start = x_start - increment
            
        elif (y < upbound and (leftbound <= x <= rightbound)):
            increment, prev_dir, prev_cnt = calculate_increment(3, prev_dir, prev_cnt)
            print("FORWARD ", increment)
            x_start = x_start + increment
        
        elif (y < upbound and x > rightbound):
            increment, prev_dir, prev_cnt = calculate_increment(4, prev_dir, prev_cnt)
            print("UP ", increment)
            z_start = z_start - increment

        elif (y > downbound and x < leftbound):
            increment, prev_dir, prev_cnt = calculate_increment(5, prev_dir, prev_cnt)
            print("DOWN ", increment)
            z_start = z_start + increment

        client.moveToPositionAsync(x_start, y_start, z_start, increment).join()

main()