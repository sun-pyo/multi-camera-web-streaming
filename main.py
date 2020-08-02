import cv2
import sys
#from mail import sendEmail
from flask import Flask, render_template, Response
from flask_basicauth import BasicAuth
import time
import threading
import imagezmq
import numpy as np
from imutils import build_montages
from datetime import datetime
import imutils
  

#email_update_interval = 600 # sends an email only once in this time interval
#video_camera = VideoCamera(flip=True) # creates a camera object, flip vertically
#object_classifier = cv2.CascadeClassifier("models/fullbody_recognition_model.xml") # an opencv classifier

# App Globals (do not edit)
app = Flask(__name__)
app.config['BASIC_AUTH_USERNAME'] = 'pi'
app.config['BASIC_AUTH_PASSWORD'] = 'pi'
app.config['BASIC_AUTH_FORCE'] = True

basic_auth = BasicAuth(app)
last_epoch = 0

first = True

@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html')

def gen():

    if first:
        imageHub = imagezmq.ImageHub()

    frameDict = {}
    lastActive = {}
    lastActiveCheck = datetime.now()

    ESTIMATED_NUM_PIS = 4
    ACTIVE_CHECK_PERIOD = 10
    ACTIVE_CHECK_SECONDS = ESTIMATED_NUM_PIS * ACTIVE_CHECK_PERIOD

    mW = 2
    mH = 2

    while True:
        (rpiName, frame) = imageHub.recv_image()
        imageHub.send_reply(b'OK')

        if rpiName not in lastActive.keys():
            print("[INFO] receiving data from {}...".format(rpiName))
          
        lastActive[rpiName] = datetime.now()


        frame = imutils.resize(frame, width=400)
        (h, w) = frame.shape[:2] 

        cv2.putText(frame, rpiName, (10, 25),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
        
        frameDict[rpiName] = frame

        montages = build_montages(frameDict.values(), (w, h), (mW, mH))

        for (i, montage) in enumerate(montages):
            ret, jpeg = cv2.imencode('.jpg',montage)
            if jpeg is not None:
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            else:
                print("frame is none")
        cv2.waitKey(1)
        if (datetime.now() - lastActiveCheck).seconds > ACTIVE_CHECK_SECONDS:
            # loop over all previously active devices
                for (rpiName, ts) in list(lastActive.items()):
                    if (datetime.now() - ts).seconds > ACTIVE_CHECK_SECONDS:
                        print("[INFO] lost connection to {}".format(rpiName))
                        lastActive.pop(rpiName)
                        frameDict.pop(rpiName)

        lastActiveCheck = datetime.now()

    cv2.destroyAllWindows()


@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, threaded=True)
