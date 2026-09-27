import cv2

video = cv2.VideoCapture("learning/test.mp4")

width = video.get(cv2.CAP_PROP_FRAME_WIDTH)
height = video.get(cv2.CAP_PROP_FRAME_HEIGHT)
fps = video.get(cv2.CAP_PROP_FPS)
frames = video.get(cv2.CAP_PROP_FRAME_COUNT)

duration = frames / fps

print("========== VIDEO INFO ==========")
print("Width:", width)
print("Height:", height)
print("FPS:", fps)
print("Frames:", frames)
print("Duration:", duration, "seconds")
video.set(cv2.CAP_PROP_POS_FRAMES, 100)
success, frame = video.read()
if success:
    cv2.imwrite("learning/frame_100.jpg", frame)
    print("Frame 100 saved successfully!")
else:
    print("Could not read frame 100.")

video.release()
video.release()