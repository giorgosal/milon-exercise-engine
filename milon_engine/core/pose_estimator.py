import os
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

_MODEL_RELATIVE_PATH = "mediapipe/modules/pose_landmark/pose_landmark_lite.tflite"


def _ensure_mediapipe_model() -> None:
    """Guarantee that mediapipe can find pose_landmark_lite.tflite.

    mediapipe 0.10.21 calls download_utils.download_oss_model() which:
      1. Resolves model_abspath = <mp_root>/<model_relative_path>
      2. Returns immediately if the file already exists there.
      3. Otherwise tries to download + write it — which fails with
         PermissionError on Streamlit Cloud (read-only venv).

    Strategy: monkey-patch download_utils so that mp_root_path points to
    a writable temp directory, then pre-populate that directory with our
    bundled copy.  mediapipe will find the file at step 2 and skip the
    download entirely.
    """
    import mediapipe.python.solutions.download_utils as _du

    # Build a writable root that mirrors what mediapipe expects:
    # <root>/mediapipe/modules/pose_landmark/pose_landmark_lite.tflite
    tmp_root = pathlib.Path("/tmp/mediapipe_models")
    target = tmp_root / _MODEL_RELATIVE_PATH
    if not target.exists():
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(_BUNDLED_MODEL, target)

    # Patch __file__ on the download_utils module so that the 4-levels-up
    # calculation inside download_oss_model() resolves to tmp_root.
    # original:  <site-packages>/mediapipe/python/solutions/download_utils.py
    # patched:   <tmp_root>/mediapipe/python/solutions/download_utils.py
    fake_file = str(
        tmp_root / "mediapipe" / "python" / "solutions" / "download_utils.py"
    )
    _du.__file__ = fake_file


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
