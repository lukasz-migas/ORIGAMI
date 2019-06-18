from datetime import datetime
import time


def getTime():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')


def ttime():
    return time.time()


def tsleep(duration=0.1):
    time.sleep(duration)
