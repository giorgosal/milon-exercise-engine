from milon_engine.core.visualizer import Visualizer
from milon_engine.core.pose_estimator import PoseEstimator
from milon_engine.exercises.base import Exercise


class FrameProcessor:
    """Coordinates pose detection → exercise logic → visualization"""

    def __init__(
        self, exercise: Exercise, pose_estimator: PoseEstimator, visualizer: Visualizer
    ):
        self.exercise = exercise
        self.pose_estimator = pose_estimator
        self.visualizer = visualizer

    def process_frame(self, frame):
        """Main pipeline"""
        # 1. Extract landmarks
        landmarks = self.pose_estimator.detect(frame)
        print(landmarks)
        if landmarks is None:
            return self.visualizer.render_no_detection(frame)

        # 2. Exercise logic
        result = self.exercise.evaluate(landmarks)

        # # 3. Visualization
        # annotated_frame = self.visualizer.render(
        #     frame,
        #     landmarks=landmarks,
        #     angle=result["angle"],
        #     reps=result["reps"],
        #     stage=result["stage"],
        #     feedback=result["feedback"],
        # )
        annotated_frame = frame
        return annotated_frame
