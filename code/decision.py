import numpy as np


# This is where you can build a decision tree for determining throttle, brake and steer 
# commands based on the output of the perception_step() function
def decision_step(Rover):

    # Implement conditionals to decide what to do given perception data
    # Here you're all set up with some basic functionality but you'll need to
    # improve on this decision tree to do a good job of navigating autonomously!

    # Example:
    # Check if we have vision data to make decisions with
    if Rover.nav_angles is not None:
        print("**********************")
        # Check for Rover.mode status
        if Rover.mode == 'forward':
            print("Decision: Sample is here " + navigable_angle(Rover.rock_angles).__str__())

            if obstacle_ahead(Rover):
                # we are too close to an obstacle, stop and turn
                Rover.mode = 'stop'

            # Check for samples ahead
            elif Rover.rock_angles.any():
                print("Decision: Sample found, distance = " + Rover.rock_dists[0].__str__())
                if Rover.rock_dists[0] < 10 or Rover.near_sample:
                    Rover.mode = "stop"
                else:
                    angle = clipped_navigable_angle(Rover.rock_angles)
                    # adjust direction
                    if np.absolute(angle) > 5 and Rover.vel > 0.6:
                        print("Decision: Sample found, breaking")
                        Rover.mode = "stop"
                    elif Rover.vel > 0.4:
                        print("Decision: Sample found, slowing down")
                        Rover.throttle = 0
                    else:
                        # and move towards the sample
                        print("Decision: Sample found, approaching")
                        Rover.brake = 0
                        Rover.throttle = 0.2
                    # lean toward the sample, instead of moving straight towards it
                    Rover.steer = angle + (clipped_navigable_angle(Rover.nav_angles))/5

            elif len(Rover.nav_angles) >= Rover.stop_forward:
                # If mode is forward, navigable terrain looks good 
                # and velocity is below max, then throttle 
                if Rover.vel < Rover.max_vel:
                    # Set throttle value to throttle setting
                    Rover.throttle = Rover.throttle_set
                else: # Else coast
                    Rover.throttle = 0
                Rover.brake = 0
                # Set steering to average angle clipped to the range +/- 15
                Rover.steer = clipped_navigable_angle(Rover.nav_angles)
            # If there's a lack of navigable terrain pixels then go to 'stop' mode
            elif len(Rover.nav_angles) < Rover.stop_forward:
                # Set mode to "stop" and hit the brakes!
                Rover.throttle = 0
                # Set brake to stored brake value
                Rover.brake = Rover.brake_set
                Rover.steer = 0
                Rover.mode = 'stop'

        # If we're already in "stop" mode then make different decisions
        elif Rover.mode == 'stop':
            # If we're in stop mode but still moving keep braking
            if Rover.vel > 0.1:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.1) then do something else
            elif Rover.vel <= 0.1:
                # Now we're stopped and we have vision data to see if there's a path forward
                print("Distance to closest obstacle " + Rover.obstacle_dists.min().__str__())
                if sample_ahead(Rover) and Rover.rock_dists[0] < 10:
                    # perform full stop to pick the sample
                    Rover.throttle = 0
                    Rover.brake = Rover.brake_set
                    Rover.steer = 0
                elif need_rotation(Rover):
                    print("Need rotation")
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    angle = -15
                    if sample_ahead(Rover):
                        angle = clipped_navigable_angle(Rover.rock_angles)
                    Rover.steer = angle
                # If we're stopped but see sufficient navigable terrain in front and no obstacles then go!
                else:
                    print("Proceed without rotation")
                    Rover.throttle = Rover.throttle_set
                    Rover.brake = 0
                    # check if we have sample in sight
                    sample_angle = clipped_navigable_angle(Rover.rock_angles)
                    if sample_angle:
                        Rover.steer = sample_angle
                    else:
                        Rover.steer = clipped_navigable_angle(Rover.nav_angles)
                    Rover.mode = 'forward'

    # Just to make the rover do something 
    # even if no modifications have been made to the code
    else:
        Rover.throttle = Rover.throttle_set
        Rover.steer = 0
        Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover

def sample_ahead(Rover):
    return Rover.rock_angles.any()

def obstacle_ahead(Rover, dist = 2):
    return len(Rover.obstacle_dists) != 0 and Rover.obstacle_dists.min() < dist

def need_rotation(Rover):
    return (sample_ahead(Rover) and navigable_angle(Rover.rock_angles) > 15) or \
            not sample_ahead(Rover) and (len(Rover.nav_angles) < Rover.go_forward or obstacle_ahead(Rover))

# use this func to determine the direction of rotation
# TODO: need a safety from rapid left-right turns
def obstacle_rotation_angle(Rover):
    print("obstacle_rotation_angle:")
    print(navigable_angle(Rover.nav_angles))
    rotateDirection = np.sign(navigable_angle(Rover.nav_angles))
    if rotateDirection == 0:  # in the off chance of this happening make a decision
        rotateDirection = 1
    print(rotateDirection * 15)
    return rotateDirection * 15

def navigable_angle(angles):
    if len(angles) == 0:
        return 0
    return np.mean(angles * 180 / np.pi)


def clipped_navigable_angle(angles):
    return np.clip(navigable_angle(angles), -15, 15)
