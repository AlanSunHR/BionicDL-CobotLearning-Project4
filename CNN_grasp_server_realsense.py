"""
This is the server running on PC for the Arcade Claw robotself.

Socket communication UR5 is implemented in ur_realtime_controller.py.
"""
from ur_realtime_controller import *
from rpy2rotationVector import rpy2rotation
import numpy as np
import pyrealsense2 as rs
from PIL import Image, ImageDraw
from predictor import Predictor
import cv2, time

# realsense
points = rs.points()
pipeline= rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.color, 1280, 720, rs.format.bgr8, 30)
config.enable_stream(rs.stream.depth, 1280, 720, rs.format.z16, 30)
profile = pipeline.start(config)
depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
align_to = rs.stream.color
align = rs.align(align_to)

# CNN model_path
NUM_BOXES = 20
WIDTH = 360
model_path = './checkpoint_100index'
CNN = Predictor(model_path)

# Start
home_joint_config = np.array([34.35, -70.59, 81.61, -101.71, -89.45, -142.52, 1])/180*3.14
for i in range(10):
    movej(home_joint_config, 0.7, 0.7)
    verifyPostion([-450, -450, 35, 2.15, -2.27, 0.02])
    rg6_close(False)
    time.sleep(3)
    frames = pipeline.wait_for_frames()
    aligned_frames = align.process(frames)
    aligned_depth_frame = aligned_frames.get_depth_frame()
    color_frame = aligned_frames.get_color_frame()
    depth_image = np.asanyarray(aligned_depth_frame.get_data())
    color_image = np.asanyarray(color_frame.get_data())
    # cv2.imshow("Image", I)
    # cv2.waitKey(0)
    # cv2.destroyAllWindows()
    color_image = cv2.cvtColor(color_image,cv2.COLOR_BGR2RGB)
    I = Image.fromarray(color_image)
    x,y,best_theta = CNN.eval(I,NUM_BOXES, WIDTH)
    M_robotToImage = np.load('M_robotToImage.npy')
    u,v,s = np.matmul(M_robotToImage, np.float32([[x, y, 1]]).transpose())
    u = u/s
    v = v/s
    draw = ImageDraw.Draw(I, 'RGBA')
    r = ((I.size[0]-WIDTH)/NUM_BOXES/2)
    draw.ellipse((u-r, v-r, u+r, v+r), (0, 0, 255, 125))
    # tranasform theta from index to [-pi, pi]
    # initial grasp plate is horizontal, clockwise rotation is positive 0 ~ pi, anti-clockwise is negative
    draw.line([(u-r*np.cos(best_theta),v-r*np.sin(best_theta)),
           (u+r*np.cos(best_theta), v+r*np.sin(best_theta))], fill=(255,255,255,125), width=10)
    I.show()
    raw_input("Please enter:")
    Rx, Ry, Rz = rpy2rotation(-3.14,-0.027,best_theta)
    movej([x, y, 0, Rx, Ry, Rz], 0.7, 0.7)
    verifyPostion([x, y, 0, Rx, Ry, Rz])
    movej([x, y, -75, Rx, Ry, Rz], 0.7, 0.7)
    verifyPostion([x, y, -75, Rx, Ry, Rz])
    rg6_close(True)
    time.sleep(3)
    movej([x, y, 50, Rx, Ry, Rz], 0.7, 0.7)
    verifyPostion([x, y, 50, Rx, Ry, Rz])
