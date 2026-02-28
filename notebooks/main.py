from milon_engine.exercises import PushUp, Exercise
from milon_engine.core.pose_estimator import PoseEstimator
from milon_engine.core.visualizer import Visualizer
from milon_engine.core import FrameProcessor
import cv2


config = "config/pushup.yaml"
pose_estimator = PoseEstimator()
# exercise = PushUp(config)
exercise = Exercise(config)
# exercise.load_calibration("pushup_calib.yaml")
visualizer = Visualizer(
    mp_drawing=pose_estimator.mp_drawing, mp_pose=pose_estimator.mp_pose
)

processor = FrameProcessor(exercise, pose_estimator, visualizer)

# Run
cap = cv2.VideoCapture(0)
while cap.isOpened():
    ret, frame = cap.read()
    if not ret:
        break

    # Single responsibility: process frame
    annotated = processor.process_frame(frame)

    cv2.imshow("Counter", annotated)
    if cv2.waitKey(10) & 0xFF == ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
