import shutil
import pathlib
import cv2
import mediapipe as mp
from typing import Optional, Tuple, Any

# Bundled model file (ships with the package so the Streamlit Cloud
# read-only venv directory never needs to be written to by mediapipe).
_BUNDLED_MODEL = (
    pathlib.Path(__file__).parent.parent / "models" / "pose_landmark_lite.tflite"
)


def _ensure_mediapipe_model() -> None:
    """Copy the bundled tflite model into the mediapipe modules directory.

    mediapipe 0.10.21 tries to download pose_landmark_lite.tflite on first
    use and cache it inside its own package directory.  On Streamlit Cloud
    that directory is read-only, which raises a PermissionError.  We
    pre-populate the target path from our bundled copy so mediapipe finds
    the file already in place and skips the download entirely.
    """
    try:
        mp_pose_dir = pathlib.Path(mp.__file__).parent / "modules" / "pose_landmark"
        target = mp_pose_dir / "pose_landmark_lite.tflite"
        if not target.exists():
            mp_pose_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(_BUNDLED_MODEL, target)
    except (OSError, PermissionError):
        # If we cannot write there either (e.g. already exists and is
        # read-only), just continue — mediapipe will find the file.
        pass


class PoseEstimator:
    """MediaPipe pose wrapper.

    Takes a BGR frame and returns pose landmarks.
    All MediaPipe-specific details are encapsulated here; callers only
    interact with detect().
    """

    def __init__(
        self,
        min_detection_conf: float = 0.5,
        min_tracking_conf: float = 0.5,
        model_complexity: int = 0,  # 0=lite, 1=full, 2=heavy
    ):
        _ensure_mediapipe_model()
        self._pose = mp.solutions.pose.Pose(
            min_detection_confidence=min_detection_conf,
            min_tracking_confidence=min_tracking_conf,
            model_complexity=model_complexity,
        )

    def detect(self, frame) -> Tuple[Optional[list], Any]:
        """Process a BGR frame and return (landmark_list, raw_results).

        - landmark_list: list of NormalizedLandmark for exercise logic,
          or None if no pose was detected.
        - raw_results:   the raw MediaPipe results object, passed to
          Visualizer.render() for skeleton drawing.
        """
        # MediaPipe requires RGB; this is an internal implementation detail
        image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        image.flags.writeable = False
        results = self._pose.process(image)
        image.flags.writeable = True

        landmarks = (
            list(results.pose_landmarks.landmark) if results.pose_landmarks else None
        )
        return landmarks, results
