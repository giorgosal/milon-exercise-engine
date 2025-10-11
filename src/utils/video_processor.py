"""Video I/O and preprocessing"""
import cv2

class VideoProcessor:
    def __init__(self, video_path):
        self.cap = cv2.VideoCapture(video_path)
        self.fps = self.cap.get(cv2.CAP_PROP_FPS)
    
    def read_frames(self):
        """Generator yielding video frames"""
        while self.cap.isOpened():
            ret, frame = self.cap.read()
            if not ret:
                break
            yield frame
