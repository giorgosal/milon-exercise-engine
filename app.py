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

# ── ICE / TURN configuration ─────────────────────────────────────────────────
# Twilio Network Traversal Service gives reliable TURN servers.
# Credentials are fetched dynamically (they expire every 24 h).
# TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set as Streamlit secrets.


def _get_rtc_configuration() -> dict:
    try:
        import urllib.request
        import json
        import base64

        sid = st.secrets["TWILIO_ACCOUNT_SID"]
        token = st.secrets["TWILIO_AUTH_TOKEN"]
        url = f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Tokens.json"
        req = urllib.request.Request(url, method="POST", data=b"")
        creds = base64.b64encode(f"{sid}:{token}".encode()).decode()
        req.add_header("Authorization", f"Basic {creds}")
        with urllib.request.urlopen(req) as r:
            data = json.loads(r.read())
        return {"iceServers": data["ice_servers"]}
    except Exception:
        # Fall back to public STUN + openrelay TURN if secrets are missing
        return {
            "iceServers": [
                {"urls": "stun:stun.l.google.com:19302"},
                {
                    "urls": "turn:openrelay.metered.ca:443?transport=tcp",
                    "username": "openrelayproject",
                    "credential": "openrelayproject",
                },
            ]
        }


RTC_CONFIGURATION = _get_rtc_configuration()

# ── Exercise selection ────────────────────────────────────────────────────────

EXERCISES = {
    "Squat": ("squat", Squat),
    "Push-up": ("pushup", PushUp),
    "Leg Raise": ("legraise", LegRaise),
}

choice = st.selectbox("Άσκηση", list(EXERCISES.keys()))
config_name, ExerciseClass = EXERCISES[choice]

# Store the current selection in session_state so the processor can read it.
st.session_state["config_name"] = config_name
st.session_state["ExerciseClass"] = ExerciseClass

# ── Video processor ───────────────────────────────────────────────────────────
# Fixed key so webrtc_streamer is never torn down on exercise change.
# The processor swaps its internal pipeline via session_state instead.


class ExerciseProcessor(VideoProcessorBase):
    def __init__(self):
        self._current_choice = st.session_state.get("config_name")
        self._build_pipeline()

    def _build_pipeline(self):
        cfg_name = st.session_state.get("config_name", "squat")
        cls = st.session_state.get("ExerciseClass", Squat)
        config = load_config(cfg_name)
        exercise = cls(config)
        self.processor = FrameProcessor(exercise, PoseEstimator(), Visualizer())

    def recv(self, frame: av.VideoFrame) -> av.VideoFrame:
        new_choice = st.session_state.get("config_name")
        if new_choice != self._current_choice:
            self._current_choice = new_choice
            self._build_pipeline()

        img = frame.to_ndarray(format="bgr24")
        annotated = self.processor.process_frame(img)
        return av.VideoFrame.from_ndarray(annotated, format="bgr24")


# ── WebRTC streamer ───────────────────────────────────────────────────────────

st.info(
    "Πάτα **START** για να ενεργοποιήσεις την κάμερα. "
    "Σταθεροποίησε τη στάση σου και το σύστημα θα ξεκινήσει αυτόματα."
)

webrtc_streamer(
    key="exercise_stream",
    video_processor_factory=ExerciseProcessor,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={"video": True, "audio": False},
    async_processing=True,
)
