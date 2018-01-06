import RPi.GPIO as GPIO 
import time GPIO.setwarnings(False) 
from picamera import PiCamera
import datetime

GPIO.setmode(GPIO.BOARD) 
PIR_PIN = 11 GPIO.setup(11, GPIO.IN) #Read output from PIR motion sensor  

def trigger_camera(PIR_PIN):  
    camera = PiCamera() 
    camera.resolution = (640, 480) 
    time_stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    video_name = "video-{}.h264".format(time_stamp)
    print("start recording for 15 seconds...") 
    camera.start_recording(video_name, format='h264') 
    camera.wait_recording(15) camera.stop_recording() 
    print("recoding ended and saved into h264_video_1.h264!")

try:  
    print "add GPIO event"  
    GPIO.add_event_detect(11, GPIO.BOTH, callback=trigger_camera)  
    while 1:  
        time.sleep(100) 
except KeyboardInterrupt:  
    print "Quit" 
finally:  GPIO.cleanup()