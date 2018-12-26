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
            # Check if there is a visible sample ahead
            print("Decision: Sample is here " + navigable_angle(Rover.rock_angles).__str__())
            if Rover.rock_angles.any():
                print("Decision: Sample found, distance = " + Rover.rock_dists[0].__str__())
                if Rover.rock_dists[0] > 10:
                    angle = clipped_navigable_angle(Rover.rock_angles)
                    # adjust direction
                    if np.absolute(angle) > 5 and Rover.vel > 0.5:
                        print("Decision: Sample found, breaking")
                        Rover.brake = Rover.brake_set / 2
                        Rover.throttle = 0
                    elif Rover.vel > 0.3:
                        print("Decision: Sample found, slowing down")
                        Rover.throttle = 0
                    else:
                        # and move towards the sample
                        print("Decision: Sample found, approaching")
                        Rover.brake = 0
                        Rover.throttle = 0.2
                    Rover.steer = angle
                else:
                    Rover.throttle = 0
                    Rover.brake = Rover.brake_set

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
            if Rover.vel > 0.2:
                Rover.throttle = 0
                Rover.brake = Rover.brake_set
                Rover.steer = 0
            # If we're not moving (vel < 0.2) then do something else
            elif Rover.vel <= 0.2:
                # Now we're stopped and we have vision data to see if there's a path forward
                if len(Rover.nav_angles) < Rover.go_forward:
                    Rover.throttle = 0
                    # Release the brake to allow turning
                    Rover.brake = 0
                    # Turn range is +/- 15 degrees, when stopped the next line will induce 4-wheel turning
                    Rover.steer = -15 # Could be more clever here about which way to turn
                # If we're stopped but see sufficient navigable terrain in front then go!
                if len(Rover.nav_angles) >= Rover.go_forward:
                    Rover.throttle = Rover.throttle_set
                    Rover.brake = 0
                    Rover.steer = clipped_navigable_angle(Rover.nav_angles)
                    Rover.mode = 'forward'
    # Just to make the rover do something 
    # even if no modifications have been made to the code
    # else:
    #    Rover.throttle = Rover.throttle_set
    #    Rover.steer = 0
    #    Rover.brake = 0
        
    # If in a state where want to pickup a rock send pickup command
    if Rover.near_sample and Rover.vel == 0 and not Rover.picking_up:
        Rover.send_pickup = True
    
    return Rover


def navigable_angle(angles):
    return np.mean(angles * 180/np.pi)


def clipped_navigable_angle(angles):
    return np.clip(navigable_angle(angles), -15, 15)
