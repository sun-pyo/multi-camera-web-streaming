import cv2
from threading import Thread
import time
import numpy as np
import sys
import time
import threading
import imagezmq
import numpy as np
from imutils import build_montages
from datetime import datetime
import imutils

class WebcamVideoStream:
    def __init__(self):
        print("init")
        self.imageHub = imagezmq.ImageHub()
        #self.frameDict = {}
        self.lastActive = {}

        self.lastActiveCheck = datetime.now()
        self.ESTIMATED_NUM_PIS = 4
        self.ACTIVE_CHECK_PERIOD = 10
        self.ACTIVE_CHECK_SECONDS = self.ESTIMATED_NUM_PIS * self.ACTIVE_CHECK_PERIOD

        self.mW = 2
        self.mH = 2
        self.w = 0
        self.h = 0

        (self.dnum, self.rpiName, self.frame) = self.imageHub.recv_image()
        self.imageHub.send_reply(b'OK')
        self.montages = self.frame
        self.stopped = False
        time.sleep(2.0)
    
    frameDict_static = {}
    dnum_static = {}
    montages_static = None
    
    def start(self):
        print("start thread")
        t = Thread(target=self.update, args=())
        t.daemon = True
        t.start()
        return self
    
    def update(self):
        print("read")
        while True:
            if self.stopped:
                return
            (self.dnum, self.rpiName, self.frame) = self.imageHub.recv_image()
            self.imageHub.send_reply(b'OK')
            self.update_dnum(self.dnum, self.rpiName)

            if self.rpiName not in self.lastActive.keys():
                print("[INFO] receiving data from {}...".format(self.rpiName))
            
            self.lastActive[self.rpiName] = datetime.now()
            
            self.frame = imutils.resize(self.frame, width=400)
            (self.h, self.w) = self.frame.shape[:2]


            # draw the sending device name on the frame
            cv2.putText(self.frame, self.rpiName, (10, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            # update the new frame in the frame dictionary
            
            self.update_frame(self.rpiName,self.frame)

            # build a montage using images in the frame dictionary
            
            #self.montages = build_montages(self.frameDict.values(), (self.w, self.h), (self.mW, self.mH))
            #self.update_montages(self.montages)

            cv2.waitKey(1)

            if (datetime.now() - self.lastActiveCheck).seconds > self.ACTIVE_CHECK_SECONDS:
                # loop over all previously active devices
                for (rpiName, ts) in list(self.lastActive.items()):
                    # remove the RPi from the last active and frame
                    # dictionaries if the device hasn't been active recently
                    if (datetime.now() - ts).seconds > self.ACTIVE_CHECK_SECONDS:
                        print("[INFO] lost connection to {}".format(rpiName))
                        self.lastActive.pop(rpiName)
                        self.frameDict.pop(rpiName)

                # set the last active check time as current time
                self.lastActiveCheck = datetime.now()

    
    @classmethod
    def update_frame(cls, name, frame):
        cls.frameDict_static[name] = frame

    @classmethod
    def update_dnum(cls, dnum, name):
        cls.dnum_static[name] = dnum

    @classmethod
    def update_montages(cls, montages):
        cls.montages_static = montages


    @classmethod
    def read_frame(cls, name):
        if name in cls.frameDict_static:
            return cls.frameDict_static[name]
        else:
            return None

    @classmethod
    def read_dnum(cls, name):
        if name in cls.dnum_static:
            return cls.dnum_static[name]
        else:
            return 0    

    @classmethod
    def read_montages(cls):
        return cls.montages_static



    def stop(self):
        self.stopped = True
    

