"""
This module calculate the perspecticve transfomation matrix from robot coordinate to image pixel coordinate

M_robotToImage * P_robot = P_image

| M11 M12 M13 |   | P1.x |   | w*P1'.x |
| M21 M22 M23 | * | P1.y | = | w*P1'.y |
| M31 M32 M33 |   | 1    |   | w*1     |

Calibration setup: camera is looking down faceing the same direction as robot
     Robot
       /\
      /  \
___________________

  point1   point4

  point2   point3
____________________
"""
import matplotlib.pyplot as plt
import numpy as np
import cv2

points_image = np.float32([[242, 202], [115, 641], [1195, 629], [1063, 167]])
points_robot = np.float32([[-265.0, -333.6], [-279.8, -619.0], [254.3, -636.12], [272.8, -336.7]])

M_robotToImage = cv2.getPerspectiveTransform(points_robot, points_image)
M_imageToRobot = cv2.getPerspectiveTransform(points_image, points_robot)

np.save('M_robotToImage', M_robotToImage)
np.save('M_imageToRobot', M_imageToRobot)

# test
M_robotToImage = np.load('M_robotToImage.npy')
M_imageToRobot = np.load('M_imageToRobot.npy')
np.matmul(M_robotToImage, np.float32([[-0.4372, -0.1535, 1]]).transpose())
np.matmul(M_imageToRobot, np.float32([[242, 202, 1]]).transpose())
