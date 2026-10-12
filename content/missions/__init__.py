"""Registry of fully-authored native mission content."""
from content.missions.i12 import MISSION as I12
from content.missions.i14 import MISSION as I14

CONTENT = {"I12": I12, "I14": I14}


def get_mission(code):
    return CONTENT.get(code)
