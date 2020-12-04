import airsim
import win32gui
import keyboard

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
    print("Setup Complete")
    prev_dir = -1
    prev_cnt = 0

    # get current drone position
    position = client.getMultirotorState().kinematics_estimated.position
    x_start = position.x_val
    y_start = position.y_val
    z_start = position.z_val 

    while(1):
        # if key is pressed stop giving inputs until key C is pressed
        # Note: key S has to be pressed (held down) until the current action has completed (this won't trigger while drone is moving)
        if keyboard.is_pressed('s'):
                while not keyboard.is_pressed('c'):
                    continue

        gaze_pos = win32gui.GetCursorPos()
        x = gaze_pos[0]
        y = gaze_pos[1]

        # look right to move right
        if (x > rightbound and (upbound <= y <= downbound)):
            increment, prev_dir, prev_cnt = calculate_increment(0, prev_dir, prev_cnt)
            print("RIGHT ", increment)
            y_start = y_start + increment
        
        # look left to move left
        elif (x < leftbound and (upbound <= y <= downbound)):
            increment, prev_dir, prev_cnt = calculate_increment(1, prev_dir, prev_cnt)
            print("LEFT ", increment)
            y_start = y_start - increment

        # look down to move backwards
        elif (y > downbound and (leftbound <= x <= rightbound)):
            increment, prev_dir, prev_cnt = calculate_increment(2, prev_dir, prev_cnt)
            print("BACKWARD ", increment)
            x_start = x_start - increment
            
        # look up to move forwards
        elif (y < upbound and (leftbound <= x <= rightbound)):
            increment, prev_dir, prev_cnt = calculate_increment(3, prev_dir, prev_cnt)
            print("FORWARD ", increment)
            x_start = x_start + increment
        
        # look top-right to move up
        elif (y < upbound and x > rightbound):
            increment, prev_dir, prev_cnt = calculate_increment(4, prev_dir, prev_cnt)
            print("UP ", increment)
            z_start = z_start - increment

        # look bottom-left to move down
        elif (y > downbound and x < leftbound):
            increment, prev_dir, prev_cnt = calculate_increment(5, prev_dir, prev_cnt)
            print("DOWN ", increment)
            z_start = z_start + increment
        
        # not a valid command, don't try to move drone
        else:
            continue

        client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()

main()