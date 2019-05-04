from PIL import Image, ImageDraw
import numpy as np
from predictor import Predictor
import glob, os

# set width of each patch and number of boxes along width direction
NUM_BOXES = 12
WIDTH = 360

# uncomment below command to run in cpu mode
# os.environ['CUDA_VISIBLE_DEVICES'] = '-1'

# load the trained network
G = Predictor('./checkpoint')

images_list = glob.glob('./test_images/*.jpg')
for j in range(len(images_list)):
    I = Image.open(images_list[j]).crop((100, 100, 1300, 1000))
    # draw sample grasp patches
    patches, boxes = G.generate_patches(I, NUM_BOXES, WIDTH)
    # calculate candicate grasp patch's best theta and probability
    candidates_theta, candidates_probability = G.eval_theta(patches)
    # select the best candicate grasp patch
    best_idx = np.argmax(candidates_probability)
    # draw the success probability
    draw = ImageDraw.Draw(I, 'RGBA')
    for i in range(len(boxes)):
        x = (boxes[i][0]+boxes[i][2])/2
        y = (boxes[i][1]+boxes[i][3])/2
        r = candidates_probability[i] * ((I.size[0]-WIDTH)/NUM_BOXES/2)
        draw.ellipse((x-r, y-r, x+r, y+r), (0, 0, 255, 125))
        if i == best_idx or candidates_probability[i]>0.5:
            # tranasform theta from index to [-pi, pi]
            # initial grasp plate is horizontal, clockwise rotation is positive 0 ~ pi, anti-clockwise is negative
            best_theta = -(-3.14 + (candidates_theta[i]-0.5)*(3.14/9))
            draw.line([(x-r*np.cos(best_theta),y-r*np.sin(best_theta)),
                   (x+r*np.cos(best_theta), y+r*np.sin(best_theta))], fill=(255,255,255,125), width=10)
    I.save('./test_images/result_'+ images_list[j][14:])
    print('Successfully analyzed image: '+ images_list[j][14:])

G.close()
