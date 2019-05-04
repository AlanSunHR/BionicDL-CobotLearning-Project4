# BionicDL-CobotLearning-Project4
The project is an Arcade Claw Robot which includes a UR5, a RG6 gripper and realsense 400 series. In the first phase of blind grasping, the robot randomly pick up toys from the working area and the grasp data is collected to train the Alexnet predicting the possibility of successful grasp. The communication between PC and robot is through socket communication. If you are doing the project with a different robot arm and communicate using ros, just add your robot arm's ROS package and lanuch the corresponding moveit group node. The CNN model for predicting the correct grasp pose is written with tensorflow.

# Project Setup
If the communication between PC and robot though ROS, make sure you've installed ROS kinetic before running the project (http://wiki.ros.org/kinetic/Installation/Ubuntu) and catkin_tools (https://catkin-tools.readthedocs.io/en/latest/installing.html).


For this setup, catkin_ws is the name of active ROS Workspace, if your workspace name is different, change the commands accordingly
If you do not have an active ROS workspace, you can create one by:
```sh
$ mkdir -p ~/catkin_ws/src
$ cd ~/catkin_ws/
$ catkin build
```

Now that you have a workspace, clone or download this repo into the src directory of your workspace:
```sh
$ cd ~/catkin_ws/src
$ git clone https://github.com/ancorasir/BionicDL-CobotLearning-Project4.git
```

Now install missing dependencies using rosdep install:
```sh
$ cd ~/catkin_ws
$ rosdep install --from-paths src --ignore-src --rosdistro=kinetic -y
```

Build the project:
```sh
$ cd ~/catkin_ws
$ catkin build aubo_msgs
$ catkin build
```

Add following to your .bashrc file:
```
source ~/catkin_ws/devel/setup.bash
```

Install tensorflow and other dependent packages:
```
pip install numpy opencv-python Pillow pyrealsense2
```
If you have GPU on your PC and have GPU driver and Cuda installed:
```
sudo pip install tensorflow-gpu==1.12
```
If you don't have GPU on your PC:
```
sudo pip install tensorflow-cpu==1.12
```

# Hand eye calibration
1. Follow BionicDL-CobotLearning-Project2 to finish the hand eye calibration.
2. (Optional) Or if the grasping only occurs on the same grasp plane (z is fixed for any grasp pose), one easier way of hand eye calibration is marking four points on the plane where the toys lying, recording the coordinates of these four points with reference to the robot (x,y) and to the camera (u,v) and using cv2.getPerspectiveTransform to compute the transformation between (x,y) and (u,v). The codes is in perspective_transform.py

# A Quick-Start: Test the pretrained model on images
In the current setting, the grasping pose only has three DoF, namely x, y, and rotation angle theta of the gripper along vertical axis. The Alexnet is train on about 10,000 images, each image is cropped such that the grasp point (x, y) is at image center. The architecture of Alexnet is slightly modified to take the rotation angle of the gripper as an auxiliary input to the model. The weighs of the CNN layers is initialed using [pretrained weights](https://tower.im/projects/f46abdb8caa1034def1078549ec46425/uploads/c3c7e7186be292b6f163ef85dc6b0ba2?version=1).

When use the pretrained model to find the best grasp pose (u,v,theta), we will slide a window of 360x360 at a certain step size on the image and sample theta every 20 degrees within -pi and pi. Then the cropped window and sampled theta is fed to the model, which will predict the possibility of successful pick up. Finally, the window and theta corresponding to the highest score will be selected.

1. Download the [pretrained model](https://tower.im/projects/f46abdb8caa1034def1078549ec46425/uploads/9b7ecf93dac71c2d4c7dc474937215ad?version=1) from tower and put the model files under ./checkpoint/ so that ./checkpoint contains four files: checkpoint, Network-400.data-00000-of-00001, Network-400.index, Network-400.meta

2. Run demo and show the best grasp pose in the image. The results are save in ./test_images
```
python grasp_image_demo.py
```

# Run the Arcade Claw robot
1. Connect the realsense to your PC.
2. Start you robot. If you are controlling the robot with ROS, lanuch your the ros node.
3. Run the grasp server. If you are using other robots, please replace the execution command in the server.
```
python CNN_grasp_server_realsense.py
```

# Train the Arcade Claw robot
If you would like to collect your own data and train your model, please refer to the data preparation and training code in ./train.
