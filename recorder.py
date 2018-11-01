import pyrealsense2 as rs
import numpy as np
import cv2

SIZE = (640, 480)
FPS = 30

MIN_DEPTH = 10
MAX_DEPTH = 50

name = '001'

# Configure depth and color streams
pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, SIZE[0], SIZE[1], rs.format.z16, FPS)
config.enable_stream(rs.stream.color, SIZE[0], SIZE[1], rs.format.bgr8, FPS)

fourcc = cv2.VideoWriter_fourcc(*'DIVX')  # 'x264' doesn't work

outRGB = cv2.VideoWriter(name + '_rgb.mp4',fourcc, FPS, (SIZE[0], SIZE[1]), True) 
outDepth = cv2.VideoWriter(name + '_dpt.mp4',fourcc, FPS, (SIZE[0], SIZE[1]), False) 

# Start streaming
pipeline.start(config)

try:
    while True:

        # Wait for a coherent pair of frames: depth and color
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            continue

        depth_image_temp = np.asanyarray(depth_frame.get_data())
        depth_image = cv2.convertScaleAbs(depth_image_temp, alpha=0.03)
        color_image = np.asanyarray(color_frame.get_data())

        depth_image[depth_image<MIN_DEPTH] = MAX_DEPTH
        depth_image[depth_image>MAX_DEPTH] = MAX_DEPTH
        depth_image -= MIN_DEPTH
        depth_image *= int((255/(MAX_DEPTH-MIN_DEPTH)))

        outRGB.write(color_image)
        outDepth.write(depth_image)

        # Stack both images horizontally
        images = np.hstack((color_image, cv2.cvtColor(depth_image,cv2.COLOR_GRAY2RGB)))

        # Show images
        cv2.namedWindow('RealSense', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('RealSense', images)
        key = cv2.waitKey(1)
        if (key & 0xFF) == ord('q'):
            break

finally:

    print('FINISH')
    pipeline.stop()
    outRGB.release()
    outDepth.release()
    cv2.destroyAllWindows()
