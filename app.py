import av
import streamlit as st
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase

from milon_engine import FrameProcessor, PoseEstimator, Visualizer, load_config
from milon_engine.exercises import Squat, PushUp, LegRaise

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(page_title="Milon Exercise Counter", layout="wide")

# ── ICE / TURN configuration ──────────────────────────────────────────────────
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

# ── Language & strings ────────────────────────────────────────────────────────

STRINGS = {
    "el": {
        "title": "Milon Exercise Counter",
        "subtitle": "Επίλεξε άσκηση, δώσε άδεια στην κάμερα και ξεκίνα!",
        "exercise_label": "Άσκηση",
        "lang_label": "Language / Γλώσσα",
        "info": (
            "Πάτα **START** για να ενεργοποιήσεις την κάμερα. "
            "Σταθεροποίησε τη στάση σου και το σύστημα θα ξεκινήσει αυτόματα."
        ),
        "instructions": {
            "Squat": (
                "**Οδηγίες**\n\n"
                "- Στάσου μπροστά από την κάμερα ώστε να φαίνεται ολόκληρο το σώμα σου.\n"
                "- Πόδια σε πλάτος ώμων.\n"
                "- Κατέβα αργά μέχρι οι μηροί να είναι παράλληλοι με το έδαφος.\n"
                "- Επέστρεψε αργά στην αρχική θέση."
            ),
            "Push-up": (
                "**Οδηγίες**\n\n"
                "- Τοποθέτησε την κάμερα στο πλάι σου ώστε να φαίνεται το σώμα σου από πλάγια.\n"
                "- Ξεκίνα σε θέση σανίδας (plank).\n"
                "- Κατέβασε το στήθος κοντά στο έδαφος.\n"
                "- Σπρώξε πίσω προς τα πάνω."
            ),
            "Leg Raise": (
                "**Οδηγίες**\n\n"
                "- Ξάπλωσε ανάσκελα μπροστά από την κάμερα.\n"
                "- Κράτα τα πόδια σου ευθεία.\n"
                "- Σήκωσε τα πόδια μέχρι 90° και κατέβασέ τα αργά.\n"
                "- Η κάμερα πρέπει να βλέπει ολόκληρο το σώμα."
            ),
        },
    },
    "en": {
        "title": "Milon Exercise Counter",
        "subtitle": "Select an exercise, allow camera access, and start!",
        "exercise_label": "Exercise",
        "lang_label": "Language / Γλώσσα",
        "info": (
            "Press **START** to activate the camera. "
            "Get into position and the system will start counting automatically."
        ),
        "instructions": {
            "Squat": (
                "**Instructions**\n\n"
                "- Stand in front of the camera so your full body is visible.\n"
                "- Feet shoulder-width apart.\n"
                "- Lower slowly until thighs are parallel to the floor.\n"
                "- Return slowly to the starting position."
            ),
            "Push-up": (
                "**Instructions**\n\n"
                "- Place the camera to your side so your body is visible in profile.\n"
                "- Start in a plank position.\n"
                "- Lower your chest close to the floor.\n"
                "- Push back up."
            ),
            "Leg Raise": (
                "**Instructions**\n\n"
                "- Lie on your back facing the camera.\n"
                "- Keep your legs straight.\n"
                "- Raise your legs to 90° then lower them slowly.\n"
                "- The camera must see your full body."
            ),
        },
    },
}

# ── Sidebar ───────────────────────────────────────────────────────────────────

with st.sidebar:
    lang = st.selectbox(
        "Language / Γλώσσα",
        options=["el", "en"],
        format_func=lambda x: "Ελληνικά" if x == "el" else "English",
        key="lang",
    )
    T = STRINGS[lang]

    st.title(T["title"])
    st.caption(T["subtitle"])
    st.divider()

    EXERCISES = {
        "Squat": ("squat", Squat),
        "Push-up": ("pushup", PushUp),
        "Leg Raise": ("legraise", LegRaise),
    }

    choice = st.selectbox(
        T["exercise_label"], list(EXERCISES.keys()), key="exercise_choice"
    )
    config_name, ExerciseClass = EXERCISES[choice]

    st.markdown(T["instructions"][choice])

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


# ── Main area ─────────────────────────────────────────────────────────────────

st.title(T["title"])
st.info(T["info"])

webrtc_streamer(
    key="exercise_stream",
    video_processor_factory=ExerciseProcessor,
    rtc_configuration=RTC_CONFIGURATION,
    media_stream_constraints={
        "video": {
            "width": {"min": 320, "ideal": 1280, "max": 1920},
            "height": {"min": 240, "ideal": 720, "max": 1080},
            "frameRate": {"ideal": 24, "max": 30},
        },
        "audio": False,
    },
    async_processing=True,
)
