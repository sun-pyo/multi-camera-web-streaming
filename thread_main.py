import cv2
import sys
#from mail import sendEmail
from flask import Flask, render_template, Response
from flask_basicauth import BasicAuth
import itertools
from flask import redirect, request, url_for
import time
import threading
import imagezmq
import numpy as np
from imutils import build_montages
from datetime import datetime
import imutils
from webcamvideostream import WebcamVideoStream

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



@app.route('/')
@basic_auth.required
def index():
    return render_template('index.html', html_dnum = WebcamVideoStream.read_dnum())

def gen():
    while True:
        montages = WebcamVideoStream.read_montages()
        for (i, montage) in enumerate(montages):
            ret, jpeg = cv2.imencode('.jpg',montage)
            if jpeg is not None:
                yield (b'--frame\r\n'
                        b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n\r\n')
            else:
                print("frame is none")
        


@app.route('/video_feed')
def video_feed():
    return Response(gen(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/drone_num')
def drone_num():
    if request.headers.get('accept') == 'text/event-stream':
        def events():
            while True:
                yield "data: %d\n\n" % (WebcamVideoStream.read_dnum())
                time.sleep(.1)  # an artificial delay
        return Response(events(), content_type='text/event-stream')
    return redirect(url_for('static', filename='index.html'))



if __name__ == '__main__':
    WebcamVideoStream().start()
    app.run(host='0.0.0.0', debug=False, threaded=True)
