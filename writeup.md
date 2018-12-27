## Project: Search and Sample Return
### Writeup Template: You can use this file as a template for your writeup if you want to submit it as a markdown file, but feel free to use some other method and submit a pdf if you prefer.

---


**The goals / steps of this project are the following:**  

**Training / Calibration**  

* Download the simulator and take data in "Training Mode"
* Test out the functions in the Jupyter Notebook provided
* Add functions to detect obstacles and samples of interest (golden rocks)
* Fill in the `process_image()` function with the appropriate image processing steps (perspective transform, color threshold etc.) to get from raw images to a map.  The `output_image` you create in this step should demonstrate that your mapping pipeline works.
* Use `moviepy` to process the images in your saved dataset with the `process_image()` function.  Include the video you produce as part of your submission.

**Autonomous Navigation / Mapping**

* Fill in the `perception_step()` function within the `perception.py` script with the appropriate image processing functions to create a map and update `Rover()` data (similar to what you did with `process_image()` in the notebook). 
* Fill in the `decision_step()` function within the `decision.py` script with conditional statements that take into consideration the outputs of the `perception_step()` in deciding how to issue throttle, brake and steering commands. 
* Iterate on your perception and decision function until your rover does a reasonable (need to define metric) job of navigating and mapping.  

[//]: # (Image References)

[original_sample]: ./calibration_images/example_rock1.jpg
[path_thresholded]: ./output/test_img_path.jpg
[obstacle_thresholded]: ./output/test_img_obstacle.jpg
[sample_thresholded]: ./output/test_img_sample.jpg
[warped_image]: ./output/warped.jpg
[warped_image_path]: ./output/warped_path.jpg
[warped_image_obstacle]: ./output/warped_obstacle.jpg
[warped_image_sample]: ./output/warped_sample.jpg

## [Rubric](https://review.udacity.com/#!/rubrics/916/view) Points
### Here I will consider the rubric points individually and describe how I addressed each point in my implementation.  

---
### Writeup / README

#### 1. Provide a Writeup / README that includes all the rubric points and how you addressed each one.  You can submit your writeup as markdown or pdf.  

You're reading it! <- true enough =)

### Notebook Analysis
#### 1. Run the functions provided in the notebook on test images (first with the test data provided, next on data you have recorded). Add/modify functions to allow for color selection of obstacles and rock samples.
Notebook can be found in submission subdirectory of this project.
Among the most important changes are: adding the threshold functions for determining obstacles and samples, named
color_thresh_dark and color_thresh_gold respectively, result of all three threshold-functions work can be seen below. 

![Original image][original_sample]
![Path image][path_thresholded]
![Obstacles image][obstacle_thresholded]
![Sample image][sample_thresholded]

#### 2. Populate the `process_image()` function with the appropriate analysis steps to map pixels identifying navigable terrain, obstacles and rock samples into a worldmap.  Run `process_image()` on your test data using the `moviepy` functions provided to create video output of your result. 
In the output/test_mapping.mp4 you can see the result of testing of all functions from the notebook.

### Autonomous Navigation and Mapping

#### 1. Fill in the `perception_step()` (at the bottom of the `perception.py` script) and `decision_step()` (in `decision.py`) functions in the autonomous mapping scripts and an explanation is provided in the writeup of how and why these functions were modified as they were.
#####perception_step():
* Initialize source and destination points for the following step
* Perform perspective transform

![Original image][original_sample]
![Warped image][warped_image]

* Apply threshold to locate available path, obstacles and sample locations if any are in sight:

![Warped image with path][warped_image_path]
![Warped image with obstacles][warped_image_obstacle]
![Warped image with samples][warped_image_sample]

* Update rover vision image to warped image to display it realtime and have information about it's sight.
* Convert the map to rover-centric coordinates of important pixels (for all 3 types). 
    
    Worth noting optimisation introduced on this step: in order to have high accuracy while performing mapping we use only the pixels closest to the rover's camera.
    Cropping of all other pixels is performed by function crop_path_data() for the path data and crop_obstacle_data() for obstacle data.
    
    Yet we still need full path data in order to make a well-weighted decision about where to go next, so we distinguish 
    path data used for mapping (xMap, yMap) and path data used for decision making (xCoord, yCoord).

* Convert rover-centric pixel values to world coordinates by rotation and relative translation.

* Update rover_state's values of world map. Note that since we can trust cropped path data, 
    we stress it so that overlapped obstacle data, if there were some by mistake, could not ruin this observation.
    
* Convert coordinates of path and samples ahead to polar coordinates and store this data into rover_state in order to 
    make a decision on where to move on next. Also print some logging info to identify if rover sees a sample.
    
    Please note newly introduced fields in Rover_state used to locate and pickup samples: rock_angles and rock_dists.
    The task could've been done without them, but that would lead to redundant computations.
    
#####decision_step():

Main changes introduced into decision_step() are targeted at sample pickup and obstacle evasion.

In mode 'forward' rover first check for an obstacles ahead and if some obstacle is too close - change mode to 'stop'.
If no obstacles ahead are too close rover checks if it can observe any samples. If sample is found rover slowly approaches 
it till comes close enough for grabbing and stops to pick the sample up.

In mode 'stop' if rover's velocity is less then 0.1 it picks one of 3 ways to proceed:
* if sample is ahead and is close enough - stay in place till the sample is picked up;
* if rover located the sample, but it's strongly off the course or if the rover can no longer move forward due to 
    absence of navigable terrain or an obstacle ahead - rover rotates in place;
* otherwise we proceed with movement towards either navigable terrain, or sample if such is visible.

Additionally several logging messages were added in order to determine the rover's behaviour accurately.
#### 2. Launching in autonomous mode your rover can navigate and map autonomously.  Explain your results and how you might improve them in your writeup.  

**Note: running the simulator with different choices of resolution and graphics quality may produce different results, particularly on different machines!  Make a note of your simulator settings (resolution and graphics quality set on launch) and frames per second (FPS output to terminal by `drive_rover.py`) in your writeup when you submit the project so your reviewer can reproduce your results.**

Launching conditions:

* Screen resolution: 1024 x 768
* Graphics quality: Fantastic
* Windowed
* FPS: 4

Decision where to move is made based on input from 3 variables:
* the location of the sample ahead - if there is one, rover stops and slowly approaches the sample till it's close 
    enough to grab it;
* the mean angle between all available for traversal pixels ahead, denoting the path rover can take and not hit into the obstacle;
* obstacles pixels ahead, which being to close to the rover show that the rover cannot continue moving forward 
    and should rotate in order to avoid collision. Used as additional safety since the mean value of navigable terrain angles
    can lead rover directly to an obstacle with plenty of visible navigable terrain on both sides of it.

## [Video Submission](https://youtu.be/cyK75L4EIwE)

Fields of improvement:

* "Rotation direction"

Current implementation whenever the rotation in place is needed performs it only in one direction. This can be improved.

* "Exploration redundancy"

Avoid already explored areas of the map based on the already mapped data. 
Can be achieved by introducing additional condition in decision-making, allowing to pick out of two ahead the path "less travelled by".
Can solve a problem with rover circling around the big chunks of terrain over and over always picking the same direction.

* "Wall crawling"

Approach of selecting the path can be changed to pick the path along the wall, improving accuracy and sample detection,
since they are located near the walls.

