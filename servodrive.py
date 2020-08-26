import time
import atexit
import sys
import termios
import contextlib
import threading
#import imutils
import RPi.GPIO as GPIO

# Import the PCA9685 module.
import Adafruit_PCA9685


class ServoMotor():
    """
    Class used for turret control.
    """    

    # freq(10) 0 ~ 180도 -> 200 ~ 690 

    def __init__(self):
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.pan_min = 363  # 60도
        self.pan_max = 526  # 120도
        self.servo_mean = 445 # 90도 
        self.tilt_min = 200 # 0도
        self.tilt_max = 690 # 180도 
        self.tiltpulse = self.servo_mean
        self.panpulse = self.servo_mean
        self.pwm.set_pwm_freq(10)
    
    def left(self):
        self.panpulse += 6
        self.pwm.set_pwm(0, 0, self.panpulse)
        time.sleep(0.001)
        print("left")
        print(self.panpulse)
        if self.panpulse > self.pan_max:
            self.panpulse = self.pan_max
        
    def right(self):
        self.panpulse -= 6
        self.pwm.set_pwm(0, 0, self.panpulse)
        time.sleep(0.001)
        print("right")
        print(self.panpulse)
        if self.panpulse < self.pan_min:
            self.panpulse = self.pan_min
        
    def stop(self):
        self.pwm.set_pwm(0, 0, 0)
        time.sleep(0.005)
        print("stop")
        
    def up(self):
        self.tiltpulse -= 5
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        time.sleep(0.001)
        print("up")
        print(self.tiltpulse)
        if self.tiltpulse < self.tilt_min:
            self.tiltpulse = self.tilt_min
        
    def down(self):
        self.tiltpulse += 5
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        time.sleep(0.001)
        print("down")
        print(self.tiltpulse)
        if self.tiltpulse > self.tilt_max:
            self.tiltpulse = self.tilt_max
            
    def reset(self):
        self.tiltpulse = self.servo_mean
        self.panpulse = self.servo_mean
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        self.pwm.set_pwm(0, 0, self.panpulse)

    def set_pulse(self, L_or_R, tilt):
        self.tiltpulse = int(tilt)
        if L_or_R == 'L':
            self.panpulse = self.pan_max
        elif L_or_R == 'R':
            self.panpulse = self.pan_min
        else:
            return

        self.pwm.set_pwm(1, 0, self.tiltpulse)
        self.pwm.set_pwm(0, 0, self.panpulse)

    def get_panpulse(self):
        return self.panpulse
    
    def get_tiltpulse(self):
        return self.panpulse
     
    





