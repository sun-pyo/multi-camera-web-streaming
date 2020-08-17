# USAGE
# python client.py --server-ip SERVER_IP

# import the necessary packages
from imutils.video import VideoStream
import imagezmq
import argparse
import socket
import time

# 서버의 ip주소를 입력 받습니다.
ap = argparse.ArgumentParser()
ap.add_argument("-s", "--server-ip", required=True,
    help="ip address of the server to which the client will connect")
args = vars(ap.parse_args())

# 입력받은 서버의 ip주소의 5555번 포트로 connect합니다.
sender = imagezmq.ImageSender(connect_to="tcp://{}:5555".format(
    args["server_ip"]))

# 위에서 설정한 hostname을 읽어내고, 영상 frame을 읽어 냅니다. 
# 카메라가 켜지는데 시간이 걸리기 때문에 warmup
rpiName = socket.gethostname()
vs = VideoStream(usePiCamera=False).start()
 #웹캠이 아니라 PiCamera일 경우 True
time.sleep(2.0)
print('start')
 
# 반복적으로 frame을 읽고 서버로 보냅니다.
while True:
    print('s2')
    frame = vs.read()
    print('send')
    mem =sender.send_image(rpiName, frame)
    print('end')
