from datetime import datetime


def getTime():
    return datetime.now().strftime('%d-%m-%Y %H:%M:%S')

