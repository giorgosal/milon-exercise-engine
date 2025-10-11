"""Joint angle calculation from pose keypoints"""
import numpy as np

def calculate_angle(point1, point2, point3):
    """Calculate angle between three points (in degrees)"""
    a = np.array(point1)
    b = np.array(point2)  # vertex
    c = np.array(point3)
    
    ba = a - b
    bc = c - b
    
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc))
    angle = np.arccos(cosine)
    return np.degrees(angle)

def get_knee_angle(landmarks):
    """Calculate knee angle from hip-knee-ankle points"""
    pass

def get_hip_angle(landmarks):
    """Calculate hip angle"""
    pass
