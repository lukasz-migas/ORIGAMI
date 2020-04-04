# Standard library imports
import time
from datetime import datetime


def get_current_time():
    return datetime.now().strftime("%d-%m-%Y %H:%M:%S")


def ttime():
    return time.time()


def tsleep(duration=0.1):
    time.sleep(duration)
