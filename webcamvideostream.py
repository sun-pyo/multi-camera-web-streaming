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
        self.imageHub = imagezmq.ImageHub('tcp://*:5555')
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

        self.Dronedata = []
        self.rpiName = None 
        self.frame = cv2.imread('no_signal.jpg')
        self.frame = imutils.resize(self.frame, width=400)
        #self.imageHub.send_reply(b'OK')
        #self.montages = self.frame
        self.stopped = False
        time.sleep(2.0)

    rectangule_color = (10, 255, 0)
    boxthickness = 3
    map_shape = (400, 400)

    Auto_mode = True

    Cam_left_right = {
        'cam1':['None', 'cam2'],
        'cam2':['cam1', 'cam3'],
        'cam3':['cam2', 'cam4'],
        'cam4':['cam3', 'None']    
    }

    Control_Dict = {
        'cam1':'None',
        'cam2':'None',
        'cam3':'None',
        'cam4':'None'
    }

    # index 0 : dnum, index 1 : ymin, index 2 : xmin, index 3: ymax, index 4 : xmax, index 5 : score, index 6 : pulse(pan, tilt)
    Dronedata_Dict = {}

    frameDict = {}
    
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
            (self.Dronedata, self.rpiName, self.frame) = self.imageHub.recv_image()

            if self.Auto_mode == True:
                self.Control_Dict[self.rpiName] = self.Control_Cam(self.rpiName)
                self.imageHub.send_reply(self.Control_Dict[self.rpiName].encode())
            elif self.Control_Dict[self.rpiName] != 'None':
                self.imageHub.send_reply(self.Control_Dict[self.rpiName].encode())
                self.Control_Dict[self.rpiName] = 'None'
            else:
                self.imageHub.send_reply(self.Control_Dict[self.rpiName].encode())
            
            self.Dronedata_Dict[self.rpiName] = self.Dronedata

            if self.rpiName not in self.lastActive.keys():
                print("[INFO] receiving data from {}...".format(self.rpiName))
            
            self.lastActive[self.rpiName] = datetime.now()
            
            #self.frame = imutils.resize(self.frame, width=400)
            (self.h, self.w) = self.frame.shape[:2]

            # update the new frame in the frame dictionary 
            self.frameDict[self.rpiName] = self.frame

            # build a montage using images in the frame dictionary
            #self.montages_static = build_montages(self.frameDict.values(), (self.w, self.h), (self.mW, self.mH))

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
                        self.Dronedata_Dict.pop(rpiName)

                # set the last active check time as current time
                self.lastActiveCheck = datetime.now()

            
    def Control_Cam(self, name):
        if name in self.Cam_left_right:
            left = self.Cam_left_right[name][0]
            right = self.Cam_left_right[name][1]
            left_dnum = 0
            right_dnum = 0
            
            if left in self.Dronedata_Dict:
                left_dnum = self.Dronedata_Dict[left][0]
            if left in self.Dronedata_Dict:
                right_dnum = self.Dronedata_Dict[right][0]
            
            if left_dnum == right_dnum:
                if left_dnum == 0:
                    return 'True 0 0'
                elif max(self.Dronedata_Dict[left][5]) > max(self.Dronedata_Dict[right][5]) and self.Dronedata_Dict[left][6][0] < 445:
                     return 'True L ' + str(self.Dronedata_Dict[left][6][1])
                elif max(self.Dronedata_Dict[right][5]) > max(self.Dronedata_Dict[left][5]) and self.Dronedata_Dict[right][6][0] > 445:
                    return 'True R ' + str(self.Dronedata_Dict[right][6][1])
                else:
                    return 'True 0 0'
            elif left_dnum > right_dnum and self.Dronedata_Dict[left][6][0] < 445:
                return 'True L ' + str(self.Dronedata_Dict[left][6][1])
            elif left_dnum < right_dnum and self.Dronedata_Dict[right][6][0] > 445:
                return 'True R ' + str(self.Dronedata_Dict[right][6][1])
            else:
                return 'True 0 0'


    @classmethod
    def move_Up(cls, name):
        if name in cls.Control_Dict and cls.Auto_mode == False:
            cls.Control_Dict[name] = 'U'
        print('U')
        
    
    @classmethod
    def move_Down(cls, name):
        if name in cls.Control_Dict and cls.Auto_mode == False:
            cls.Control_Dict[name] = 'D'
        print('D')
        
    
    @classmethod
    def move_Right(cls, name):
        if name in cls.Control_Dict and cls.Auto_mode == False:
            cls.Control_Dict[name] = 'R'
        print('R')
        

    @classmethod
    def move_Left(cls, name):
        if name in cls.Control_Dict and cls.Auto_mode == False:
            cls.Control_Dict[name] = 'L'
        print('L')
        
    @classmethod
    def move_Init(cls, name):
        if name in cls.Control_Dict and not cls.Auto_mode:
            cls.Control_Dict[name] = 'C'
        print('C')
        


    @classmethod
    def read_frame(cls, name):
        if name in cls.frameDict:
            frame = cls.frameDict[name].copy()
            if int(cls.Dronedata_Dict[name][0]) > 0:
                scores = list(map(float, cls.Dronedata_Dict[name][5]))
                ymin = cls.Dronedata_Dict[name][1]
                xmin = cls.Dronedata_Dict[name][2]
                ymax = cls.Dronedata_Dict[name][3]
                xmax = cls.Dronedata_Dict[name][4]
                for i in range(len(scores)):
                    if ((scores[i] > 0.5) and (scores[i] <= 1.0)):

                        cv2.rectangle(frame, (xmin[i],ymin[i]), (xmax[i],ymax[i]), cls.rectangule_color, cls.boxthickness)  #xmax = x+w ymax = y+h 
                        # Draw label
                        #object_name = labels[int(classes[i])] # Look up object name from "labels" array using class index
                        #print('Number of Drone', len(num))
                        label = '%s: %d%%' % ('Drone', int(scores[i]*100)) # Example: 'person: 72%' #object_name
                        labelSize, baseLine = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.7, 2) # Get font size
                        label_ymin = max(ymin[i], labelSize[1] + 10) # Make sure not to draw label too close to top of window
                        cv2.rectangle(frame, (xmin[i], label_ymin-labelSize[1]-10), (xmin[i]+labelSize[0], label_ymin+baseLine-10), (255, 255, 255), cv2.FILLED) # Draw white box to put label text in
                        cv2.putText(frame, label, (xmin[i], label_ymin-7), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2) # Draw label text
                    
            # draw the sending device name on the frame
            cv2.putText(frame, name, (380, 25),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            frame = imutils.resize(frame, width=400)
            return frame
        else:
            default_frame = cv2.imread('no_signal.jpg')
            default_frame = imutils.resize(default_frame, width=400)
            return default_frame

    @classmethod
    def read_dnum(cls, name):
        if name in cls.Dronedata_Dict:
            return int(cls.Dronedata_Dict[name][0])
        else:
            return 0    

    @classmethod
    def send_frame(cls, name, adress):
        if name in cls.frameDict:
            print('send img')
            sender = imagezmq.ImageSender("tcp://{}:5001".format(adress))
            mem= cls.sender.send_image(list(cls.Dronedata_Dict[name]),name, cls.frameDict[name])

    @classmethod
    def AutoMode_Flag(cls):
        if cls.Auto_mode == True:
            cls.Auto_mode = False
        else:
            cls.Auto_mode = True

        return cls.Auto_mode

    
            
    def stop(self):
        self.stopped = True
    

