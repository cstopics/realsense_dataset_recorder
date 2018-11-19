import pyrealsense2 as rs
import numpy as np
import cv2

SIZE = (640, 480)
FPS = 30

MIN_DEPTH = 100
MAX_DEPTH = 200

SHOW_MASKED = False

pipeline = rs.pipeline()
config = rs.config()
config.enable_stream(rs.stream.depth, SIZE[0], int(0.75*SIZE[1]), rs.format.z16, FPS)
config.enable_stream(rs.stream.color, SIZE[0], SIZE[1], rs.format.bgr8, FPS)

profile = pipeline.start(config)
align = rs.align(rs.stream.color)

depth_sensor = profile.get_device().first_depth_sensor()
depth_scale = depth_sensor.get_depth_scale()
print("Depth Scale is: " , depth_scale)

min_depth_data = int(MIN_DEPTH*0.01 / depth_scale)
max_depth_data = int(MAX_DEPTH*0.01 / depth_scale)

clipping_distance_in_meters = 1 #1 meter
clipping_distance = clipping_distance_in_meters / depth_scale



try:
    while True:
        frames = pipeline.wait_for_frames()
        aligned_frames = align.process(frames)
        
        aligned_depth_frame = aligned_frames.get_depth_frame()
        color_frame = aligned_frames.get_color_frame()
        
        if not aligned_depth_frame or not color_frame:
            continue
        
        depth_image_temp = np.asanyarray(aligned_depth_frame.get_data())
        depth_image = np.asanyarray(aligned_depth_frame.get_data())
        color_image = np.asanyarray(color_frame.get_data())

        depth_image_3d = np.dstack((depth_image_temp, depth_image_temp, depth_image_temp))	
        depth_image_temp[depth_image_temp<min_depth_data] = max_depth_data
        depth_image_temp[depth_image>max_depth_data] = max_depth_data
        depth_image_temp -= min_depth_data
        depth_image_temp = 255.0 * (depth_image_temp.astype(np.float) / (max_depth_data-min_depth_data))
        depth_image = depth_image_temp.astype(np.uint8)
        
        grey_color = 153
        masked = np.where((depth_image_3d > max_depth_data) | (depth_image_3d < min_depth_data), grey_color, color_image)

        color_image_show = cv2.flip( color_image, 1 )
        masked_show = cv2.flip( masked, 1 )
        depth_image_show = cv2.flip( depth_image, 1 )

        if SHOW_MASKED:
        	images = np.hstack((masked_show, cv2.cvtColor(depth_image_show,cv2.COLOR_GRAY2RGB)))
        else:
        	images = np.hstack((color_image_show, cv2.cvtColor(depth_image_show,cv2.COLOR_GRAY2RGB)))
        cv2.namedWindow('Align Example', cv2.WINDOW_AUTOSIZE)
        cv2.imshow('Align Example', images)
        key = cv2.waitKey(1)

        if key & 0xFF == ord('q') or key == 27:
            cv2.destroyAllWindows()
            break
finally:
    pipeline.stop()