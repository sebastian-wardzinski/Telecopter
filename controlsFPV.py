import airsim
import win32gui
import keyboard
import math

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

base_speed = 5
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
        0: "Rotate Right",
        1: "Rotate Left",
        2: "Move Forward",
        3: "Move Up",
        4: "Move Down"
    }

    print(switcher.get(prev_dir, "Invalid"), " ", increment)


def main():
    print("Setup Complete")
    prev_dir = -1
    prev_cnt = 0

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

        # look up to move forwards
        ## WARNING, BUGS IF YOU END UP SPINNING A LOT (MORE THAN A ROTATION OVERALL)
        elif (y < upbound and (leftbound <= x <= rightbound)):
            increment, prev_dir, prev_cnt = calculate_increment(2, prev_dir, prev_cnt)
            yaw  = math.acos(client.getMultirotorState().kinematics_estimated.orientation.w_val) * 2
            x_start += math.cos(yaw) * increment
            y_start -= math.sin(yaw) * increment
            client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()            

        # look bottom-right to move up
        elif (y > upbound and x > rightbound):
            increment, prev_dir, prev_cnt = calculate_increment(3, prev_dir, prev_cnt)
            z_start = z_start - increment
            client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()

        # look bottom-left to move down
        elif (y > upbound and x < leftbound):
            increment, prev_dir, prev_cnt = calculate_increment(4, prev_dir, prev_cnt)
            z_start = z_start + increment
            client.moveToPositionAsync(x_start, y_start, z_start, increment, 5).join()
       
        else:
            continue
        
        print_command(prev_dir, increment)
        
main()