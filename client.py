import socket
import time
import numpy as np
import sys
import importlib.util
import argparse
from servodrive import ServoMotor
#from imutils.video import VideoStream
import os
from videostream import VideoStream
import imagezmq
import cv2
import RPi.GPIO as GPIO
import termios
import contextlib
from servodrive import ServoMotor


# Define and parse input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--modeldir', help='Folder the .tflite file is located in',
                    required=True)
parser.add_argument('--graph', help='Name of the .tflite file, if different than detect.tflite',
                    default='detect.tflite')
parser.add_argument('--labels', help='Name of the labelmap file, if different than labelmap.txt',
                    default='labelmap.txt')
parser.add_argument('--threshold', help='Minimum confidence threshold for displaying detected objects',
                    default=0.5)
parser.add_argument('--resolution', help='Desired webcam resolution in WxH. If the webcam does not support the resolution entered, errors may occur.',
                    default='800x600')
parser.add_argument('--edgetpu', help='Use Coral Edge TPU Accelerator to speed up detection',
                    action='store_true')
parser.add_argument("-s", "--server", required=True,
    help="ip address of the server to which the client will connect")

args = parser.parse_args()

MODEL_NAME = args.modeldir
GRAPH_NAME = args.graph
LABELMAP_NAME = args.labels
min_conf_threshold =0.5
resW, resH = args.resolution.split('x')
imW, imH = int(resW), int(resH)
use_TPU = args.edgetpu

# Import TensorFlow libraries
# If tflite_runtime is installed, import interpreter from tflite_runtime, else import from regular tensorflow
# If using Coral Edge TPU, import the load_delegate library
pkg = importlib.util.find_spec('tflite_runtime')
if pkg:
    from tflite_runtime.interpreter import Interpreter
    if use_TPU:
        from tflite_runtime.interpreter import load_delegate
else:
    from tensorflow.lite.python.interpreter import Interpreter
    if use_TPU:
        from tensorflow.lite.python.interpreter import load_delegate

# If using Edge TPU, assign filename for Edge TPU model
if use_TPU:
    # If user has specified the name of the .tflite file, use that name, otherwise use default 'edgetpu.tflite'
    if (GRAPH_NAME == 'detect.tflite'):
        GRAPH_NAME = 'edgetpu.tflite'       

# Get path to current working directory
CWD_PATH = os.getcwd()

# Path to .tflite file, which contains the model that is used for object detection
PATH_TO_CKPT = os.path.join(CWD_PATH,MODEL_NAME,GRAPH_NAME)

# Path to label map file
PATH_TO_LABELS = os.path.join(CWD_PATH,MODEL_NAME,LABELMAP_NAME)

# Load the label map
with open(PATH_TO_LABELS, 'r') as f:
    labels = [line.strip() for line in f.readlines()]

# Have to do a weird fix for label map if using the COCO "starter model" from
# https://www.tensorflow.org/lite/models/object_detection/overview
# First label is '???', which has to be removed.
if labels[0] == '???':
    del(labels[0])

# Load the Tensorflow Lite model.
# If using Edge TPU, use special load_delegate argument
if use_TPU:
    interpreter = Interpreter(model_path=PATH_TO_CKPT,
                              experimental_delegates=[load_delegate('libedgetpu.so.1.0')])
    #print(PATH_TO_CKPT)
else:
    interpreter = Interpreter(model_path=PATH_TO_CKPT)

interpreter.allocate_tensors()

# Get model details
input_details = interpreter.get_input_details()
output_details = interpreter.get_output_details()
height = input_details[0]['shape'][1]
width = input_details[0]['shape'][2]

floating_model = (input_details[0]['dtype'] == np.float32)

input_mean = 127.5
input_std = 127.5
s= ServoMotor()

# Initialize frame rate calculation
frame_rate_calc = 1
freq = cv2.getTickFrequency()

dnum=0
time_appear_drone = 0
boxthickness = 3
linethickness = 2
# Initialize video stream
#videostream = VideoStream(resolution=(800,600),framerate=30).start()

rectangule_color = (10, 255, 0)


sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(args.server))
rpi_name = socket.gethostname() # send RPi hostname with each image
picam = VideoStream(resolution=(imW,imH),framerate=30).start()
print(picam.read().shape)
time.sleep(1.0)  # allow camera sensor to warm up
frame1 = picam.read()
rows, cols, _ = frame1.shape
x_medium = int(cols / 2)
x_center = int(cols / 2)
y_medium = int(rows / 2)
y_center = int(rows / 2)

while True:  # send images as stream until Ctrl-C
  # Start timer (for calculating frame rate)
  t1 = cv2.getTickCount()
  frame1 = picam.read()
  # Acquire frame and resize to expected shape [1xHxWx3]
  frame = frame1.copy()
  frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
  frame_resized = cv2.resize(frame_rgb, (width, height))
  input_data = np.expand_dims(frame_resized, axis=0)

# Normalize pixel values if using a floating model (i.e. if model is non-quantized)
  if floating_model:
    input_data = (np.float32(input_data) - input_mean) / input_std
# Perform the actual detection by running the model with the image as input
  interpreter.set_tensor(input_details[0]['index'],input_data)
  interpreter.invoke()

  # Retrieve detection results
  boxes = interpreter.get_tensor(output_details[0]['index'])[0] # Bounding box coordinates of detected objects
  classes = interpreter.get_tensor(output_details[1]['index'])[0] # Class index of detected objects
  scores = interpreter.get_tensor(output_details[2]['index'])[0] # Confidence of detected objects
  #num = interpreter.get_tensor(output_details[3]['index'])[0]  # Total number of detected objects (inaccurate and not needed)
  num = []
  ymin = []
  xmin = []
  ymax = []
  xmax = []
  Drone_data = []
# Loop over all detections and draw detection box if confidence is above minimum threshold
  for i in range(len(scores)):
    if ((scores[i] > min_conf_threshold) and (scores[i] <= 1.0)):
      # Get bounding box coordinates and draw box
      # Interpreter can return coordinates that are outside of image dimensions, need to force them to be within image using max() and min()
      ymin.append(int(max(1,(boxes[i][0] * imH))))
      xmin.append(int(max(1,(boxes[i][1] * imW))))
      ymax.append(int(min(imH,(boxes[i][2] * imH))))
      xmax.append(int(min(imW,(boxes[i][3] * imW))))
      num.append(str(scores[i]))
                
  if len(num) != 0:
    most = num.index(max(num))
    lx = int(max(1,(boxes[most][1] * imW)))
    ly = int(max(1,(boxes[most][0] * imH)))
    lw = int(min(imW,(boxes[most][3] * imW)))
    lh = int(min(imH,(boxes[most][2] * imH)))
    x_medium = int((lx+lw)/2)
    y_medium = int((ly+lh)/2)
    D = lw-lx
    print(D)
    distance = round(((-(6/5)*D+268) / 100),2)
    if distance < 0:
        distance = 0.2

    if x_medium < x_center - 60:
        s.left()
    elif x_medium > x_center + 60:
        s.right()
    else :
        s.stop()
        
    if y_medium < y_center - 30:
        s.up()
    elif y_medium > y_center + 30:
        s.down()
        
  Drone_data.append(len(num))
  Drone_data.append(ymin)
  Drone_data.append(xmin)
  Drone_data.append(ymax)
  Drone_data.append(xmax)
  Drone_data.append(num)

  mes = sender.send_image(Drone_data, rpi_name, frame)
  message = mes.decode()

  if len(num) == 0:
        if message == 'R':
            s.right()
        elif message == 'L':
            s.left()

  

  # Calculate framerate
  t2 = cv2.getTickCount()
  time1 = (t2-t1)/freq
  frame_rate_calc= 1/time1   

  # Press 'q' to quit
  if cv2.waitKey(1) == ord('q'):
      break
