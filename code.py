from picamera import PiCamera
import shlex, subprocess, os

camera = PiCamera()
# max resolution is (3280, 2464) for full FoV at 15FPS
camera.resolution = (1640, 1232)
# zoom (x, y, w, h) proportion of the image to include in the output
# use the following to crop 4:3 full FoV res when using 16:9 resize res to achieve full width sensor FoV
#camera.zoom = (0.0, 0.1, 1.0, 0.75)
camera.framerate = 30
#camera.rotation = 180

# High Quality Stream
HQcmd = "gst-launch-1.0 fdsrc ! h264parse ! rtspclientsink location=rtsp://myuser:mypass@localhost:8554/hqstream debug=false"
HQcmd = shlex.split(HQcmd)
gstreamerHQ = subprocess.Popen(HQcmd, stdin=subprocess.PIPE)
# Low Quality Stream
LQcmd = "gst-launch-1.0 fdsrc ! h264parse ! rtspclientsink location=rtsp://myuser:mypass@localhost:8554/lqstream debug=false"
LQcmd = shlex.split(LQcmd)
gstreamerLQ = subprocess.Popen(LQcmd, stdin=subprocess.PIPE)

try:
    camera.start_recording(gstreamerHQ.stdin, splitter_port=1, format='h264', profile='high', intra_period=30, quality=30, sei=True, sps_timing=True)
    camera.start_recording(gstreamerLQ.stdin, splitter_port=2, format='h264', profile='high', intra_period=30, quality=30, sei=True, sps_timing=True, resize=(640, 480))
    while True:
        camera.wait_recording(timeout=1, splitter_port=1)
        camera.wait_recording(timeout=1, splitter_port=2)
        camera.capture('/dev/shm/camera-tmp.jpg', use_video_port=True, resize=(800, 600))
        os.rename('/dev/shm/camera-tmp.jpg', '/dev/shm/camera.jpg') # make image replacement atomic operation
except KeyboardInterrupt:
    camera.stop_recording(splitter_port=1)
    camera.stop_recording(splitter_port=2)
    gstreamerHQ.stdin.close()
    gstreamerLQ.stdin.close()
    gstreamerHQ.wait()
    gstreamerLQ.wait()
