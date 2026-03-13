import av
import cv2
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

from milon_engine import FrameProcessor, PoseEstimator, Visualizer, load_config
from milon_engine.exercises import Squat, PushUp, LegRaise

# ── Page config ──────────────────────────────────────────────────────────────

st.set_page_config(page_title="Milon Exercise Counter", layout="centered")
st.title("Milon Exercise Counter")
st.write("Επίλεξε άσκηση, δώσε άδεια στην κάμερα και ξεκίνα!")

# ── Exercise selection ────────────────────────────────────────────────────────

EXERCISES = {
    "Squat": ("squat", Squat),
    "Push-up": ("pushup", PushUp),
    "Leg Raise": ("legraise", LegRaise),
}

choice = st.selectbox("Άσκηση", list(EXERCISES.keys()))
config_name, ExerciseClass = EXERCISES[choice]

# ── Video processor ───────────────────────────────────────────────────────────
# Ένα νέο αντικείμενο δημιουργείται κάθε φορά που αλλάζει η επιλογή άσκησης.


class ExerciseProcessor(VideoProcessorBase):
    def __init__(self):
        config = load_config(config_name)
        exercise = ExerciseClass(config)
        self.processor = FrameProcessor(exercise, PoseEstimator(), Visualizer())

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        # Μετατροπή frame σε BGR (format που περιμένει το OpenCV)
        img = frame.to_ndarray(format="bgr24")

        # Εκτέλεση pipeline
        annotated = self.processor.process_frame(img)

        # Επιστροφή annotated frame στον browser
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")


# ── WebRTC streamer ───────────────────────────────────────────────────────────
# ICE servers: Google STUN + open-relay.metered.ca TURN (free, no account needed).
# TURN is required on Streamlit Cloud because the server sits behind a firewall
# and peer-to-peer WebRTC connections cannot be established with STUN alone.

RTC_CONFIGURATION = {
    "iceServers": [
        {"urls": "stun:stun.l.google.com:19302"},
        {
            "urls": "turn:openrelay.metered.ca:80",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": "turn:openrelay.metered.ca:443",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
        {
            "urls": "turn:openrelay.metered.ca:443?transport=tcp",
            "username": "openrelayproject",
            "credential": "openrelayproject",
        },
    ]
}

st.info(
    "Πάτα **START** για να ενεργοποιήσεις την κάμερα. "
    "Σταθεροποίησε τη στάση σου και το σύστημα θα ξεκινήσει αυτόματα."
)

webrtc_streamer(
    key=choice,  # το key αλλάζει όταν αλλάζει η άσκηση,
    # ώστε να ξαναδημιουργηθεί ο processor
    video_processor_factory=ExerciseProcessor,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)
