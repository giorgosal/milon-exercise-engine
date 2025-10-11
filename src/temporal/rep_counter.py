"""Repetition counting using temporal patterns"""
import numpy as np
from scipy.signal import find_peaks

class RepCounter:
    def __init__(self, exercise_type):
        self.exercise_type = exercise_type
        self.count = 0
    
    def count_reps(self, angle_sequence):
        """Count repetitions from joint angle time series"""
        peaks, _ = find_peaks(angle_sequence, height=0, distance=20)
        return len(peaks)
    
    def detect_phases(self, pose_sequence):
        """Detect concentric/eccentric phases"""
        pass
