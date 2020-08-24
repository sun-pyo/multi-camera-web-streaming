import numpy as np
import cv2
import math

r = 50

img = np.zeros((400,400,3),np.uint8)
img = cv2.ellipse(img,(60,70),(r,r),0,-120,60-120,(0,255,0),2)

img = cv2.line(img,(60,70),(60-25,int(70-25*math.sqrt(3))), (0,255,0),2)
img = cv2.line(img,(60,70),(60+25,int(70-25*math.sqrt(3))), (0,255,0),2)
cv2.imshow(" ",img)
cv2.waitKey(1000)