import pytest
import numpy as np
from src.biomechanics.angles import calculate_angle

def test_calculate_angle():
    # Test 90 degree angle
    p1 = [0, 1]
    p2 = [0, 0]
    p3 = [1, 0]
    assert abs(calculate_angle(p1, p2, p3) - 90.0) < 1e-6

def test_calculate_angle_180():
    # Test straight line (180 degrees)
    p1 = [0, 0]
    p2 = [1, 0]
    p3 = [2, 0]
    assert abs(calculate_angle(p1, p2, p3) - 180.0) < 1e-6
