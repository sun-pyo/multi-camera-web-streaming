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

# "0"(1.5ms 펄스)은 중간, "90"(~ 2ms 펄스)은 오른쪽 끝, "-90"(~ 1ms 펄스)은 왼쪽 끝

class ServoMotor():
    """
    Class used for turret control.
    """
    def __init__(self):
        self.pwm = Adafruit_PCA9685.PCA9685()
        self.servo_min = 5  # Min pulse length out of 4096
        self.servo_max = 600  # Max pulse length out of 4096
        self.pwm.set_pwm_freq(10)
        self.tiltpulse = 580
        self.panpulse = 380
        #self.p.ChangeDutyCycle(5.5)
        
        
    
    def left(self):
        self.panpulse -= 6
        self.pwm.set_pwm(0, 0, self.panpulse)
        #time.sleep(0.001)
        print("left")
        print(self.panpulse)
        if self.panpulse < 120:
            self.panpulse = 120
        
    def right(self):
        self.panpulse += 6
        self.pwm.set_pwm(0, 0, self.panpulse)
        #time.sleep(0.01)
        print("right")
        print(self.panpulse)
        if self.panpulse > 680:
            self.panpulse = 680
        
    def stop(self):
        pwm.set_pwm(0, 0, 0)
        time.sleep(0.005)
        print("stop")
        
    def up(self):
        self.tiltpulse -= 5
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        #time.sleep(0.01)
        print("up")
        print(self.tiltpulse)
        if self.tiltpulse < 100:
            self.tiltpulse = 100
        
    def down(self):
        self.tiltpulse += 5
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        #time.sleep(0.01)
        print("down")
        print(self.tiltpulse)
        if self.tiltpulse > 700:
            self.tiltpulse = 700
            
    def reset(self):
        self.tiltpulse = 580
        self.panpulse = 380
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        self.pwm.set_pwm(0, 0, self.panpulse)

    def set_pulse(self, tilt, pan):
        self.tiltpulse = tilt
        self.panpulse = pan
        self.pwm.set_pwm(1, 0, self.tiltpulse)
        self.pwm.set_pwm(0, 0, self.panpulse)

     
    





