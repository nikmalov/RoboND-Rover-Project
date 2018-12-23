import numpy as np
import cv2

# Identify pixels above the threshold
# Threshold of RGB > 160 does a nice job of identifying ground pixels only
def color_thresh(img, rgb_thresh=(160, 160, 160)):
    # Create an array of zeros same xy size as img, but single channel
    color_select = np.zeros_like(img[:,:,0])
    # Require that each pixel be above all three threshold values in RGB
    # above_thresh will now contain a boolean array with "True"
    # where threshold was met
    above_thresh = (img[:,:,0] > rgb_thresh[0]) \
                & (img[:,:,1] > rgb_thresh[1]) \
                & (img[:,:,2] > rgb_thresh[2])
    # Index the array of zeros with the boolean array and set to 1
    color_select[above_thresh] = 1
    # Return the binary image
    return color_select

def color_thresh_gold(img):
    binaryImg = np.zeros_like(img[:,:,0])
    for i in range(img.shape[0]):
        for j in range(img.shape[1]):
            binaryImg[i,j] = img[i,j,0] > 60 and img[i,j,1] > 60 and img[i,j,2] < 30
    return binaryImg

def color_thresh_dark(img, thresh = 115):
    color_select = np.zeros_like(img[:,:,0])
    above_thresh = (img[:,:,0] < thresh) \
                & (img[:,:,1] < thresh) \
                & (img[:,:,2] < thresh)
    color_select[above_thresh] = 1
    return color_select

# Define a function to convert from image coords to rover coords
def rover_coords(binary_img):
    # Identify nonzero pixels
    ypos, xpos = binary_img.nonzero()
    # Calculate pixel positions with reference to the rover position being at the 
    # center bottom of the image.  
    x_pixel = -(ypos - binary_img.shape[0]).astype(np.float)
    y_pixel = -(xpos - binary_img.shape[1]/2 ).astype(np.float)
    return x_pixel, y_pixel


# Define a function to convert to radial coords in rover space
def to_polar_coords(x_pixel, y_pixel):
    # Convert (x_pixel, y_pixel) to (distance, angle) 
    # in polar coordinates in rover space
    # Calculate distance to each pixel
    dist = np.sqrt(x_pixel**2 + y_pixel**2)
    # Calculate angle away from vertical for each pixel
    angles = np.arctan2(y_pixel, x_pixel)
    return dist, angles

# Define a function to map rover space pixels to world space
def rotate_pix(xpix, ypix, yaw):
    # Convert yaw to radians
    yaw_rad = yaw * np.pi / 180
    xpix_rotated = (xpix * np.cos(yaw_rad)) - (ypix * np.sin(yaw_rad))
                            
    ypix_rotated = (xpix * np.sin(yaw_rad)) + (ypix * np.cos(yaw_rad))
    # Return the result  
    return xpix_rotated, ypix_rotated

def translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale): 
    # Apply a scaling and a translation
    xpix_translated = (xpix_rot / scale) + xpos
    ypix_translated = (ypix_rot / scale) + ypos
    # Return the result  
    return xpix_translated, ypix_translated


# Define a function to apply rotation and translation (and clipping)
# Once you define the two functions above this function should work
def pix_to_world(xpix, ypix, xpos, ypos, yaw, world_size, scale):
    # Apply rotation
    xpix_rot, ypix_rot = rotate_pix(xpix, ypix, yaw)
    # Apply translation
    xpix_tran, ypix_tran = translate_pix(xpix_rot, ypix_rot, xpos, ypos, scale)
    # Perform rotation, translation and clipping all at once
    x_pix_world = np.clip(np.int_(xpix_tran), 0, world_size - 1)
    y_pix_world = np.clip(np.int_(ypix_tran), 0, world_size - 1)
    # Return the result
    return x_pix_world, y_pix_world

# Define a function to perform a perspective transform
def perspect_transform(img, src, dst):
    M = cv2.getPerspectiveTransform(src, dst)
    warped = cv2.warpPerspective(img, M, (img.shape[1], img.shape[0]))# keep same size as input image
    return warped

# Crops path data to only the most trusted visible part
def crop_path_data(binaryImg):
    size = binaryImg.shape
    result = np.zeros_like(binaryImg)
    for i in range(int(19.3*size[0]/20), size[0]):
        for j in range(int(9.9*size[1]/20), int(10.1*size[1]/20)):
            result[i,j] = binaryImg[i,j]
    return result

def crop_obstacle_data(binaryImg):
    size = binaryImg.shape
    result = np.zeros_like(binaryImg)
    for i in range(int(17*size[0]/20), size[0]):
        for j in range(int(9.2*size[1]/20), int(10.8*size[1]/20)):
            result[i,j] = binaryImg[i,j]
    return result



# Apply the above functions in succession and update the Rover state accordingly
def perception_step(Rover):
    # Perform perception steps to update Rover()
    # 1) Define source and destination points for perspective transform
    dst_size = 5
    bottom_offset = 0
    source = np.float32([[28, 134], [272, 132], [194, 96], [119 ,96]])
    size = Rover.img.shape
    destination = np.float32([[size[1]/2 - dst_size, size[0] - bottom_offset],
                  [size[1]/2 + dst_size, size[0] - bottom_offset],
                  [size[1]/2 + dst_size, size[0] - 2*dst_size - bottom_offset],
                  [size[1]/2 - dst_size, size[0] - 2*dst_size - bottom_offset],
                  ])
    # 2) Apply perspective transform
    warped = perspect_transform(Rover.img, source, destination)
    # 3) Apply color threshold to identify navigable terrain/obstacles/rock samples
    threshedPath = color_thresh(warped)
    threshedGold = color_thresh_gold(warped)
    threshedObstacle = crop_obstacle_data(color_thresh_dark(warped))
    # 4) Update Rover.vision_image (this will be displayed on left side of screen)
    #Rover.vision_image[:,:,0] = threshedObstacle
    #Rover.vision_image[:,:,1] = threshedGold
    #Rover.vision_image[:,:,2] = threshedPath
    Rover.vision_image = warped
    # 5) Convert map image pixel values to rover-centric coords
    xObstacle, yObstacle = rover_coords(threshedObstacle)
    xGold, yGold = rover_coords(threshedGold)
    #we use full picture to make a further decision
    xCoord, yCoord = rover_coords(threshedPath)
    #but use cropped picture to map surroundings
    xMap, yMap = rover_coords(crop_path_data(threshedPath))
    # 6) Convert rover-centric pixel values to world coordinates
    side = Rover.worldmap.shape[0]
    xObstacleWorld, yObstacleWorld = pix_to_world(xObstacle, yObstacle, Rover.pos[0], Rover.pos[1], Rover.yaw, side, 1)
    xGoldWorld, yGoldWorld = pix_to_world(xGold, yGold, Rover.pos[0], Rover.pos[1], Rover.yaw, side, 1)
    xWorld, yWorld = pix_to_world(xMap, yMap, Rover.pos[0], Rover.pos[1], Rover.yaw, side, 1)
    # 7) Update Rover worldmap (to be displayed on right side of screen)
    Rover.worldmap[yObstacleWorld, xObstacleWorld, 0] += 1
    Rover.worldmap[yGoldWorld, xGoldWorld, 1] += 1
    Rover.worldmap[yWorld, xWorld, 2] += 100 # stress it, since it's a reliable data
    # 8) Convert rover-centric pixel positions to polar coordinates
    dist, angle = to_polar_coords(xCoord, yCoord)
    rockDist, rockAngle = to_polar_coords(xGold, yGold)
    # Update Rover pixel distances and angles
    Rover.nav_dists = dist
    Rover.nav_angles = angle
    #point to visible sample if such exists
    Rover.rock_dists = rockDist
    Rover.rock_angles = rockAngle
    print("Updated: Sample is here " + rockAngle.__str__())
    return Rover
