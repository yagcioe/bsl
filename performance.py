import inspect
import time as t

times = {}
startTimes = {}


def start(name=None):
    f = getFunctionName(name)
    curTime = t.process_time_ns()
    startTime = startTimes.get(f, -1)
    if startTime != -1:
        print('overriding start time beovore ending for '+f)
    startTimes[f] = curTime


def end(name=None):
    f = getFunctionName(name)
    curTime = t.process_time_ns()
    startTime = startTimes.get(f, -1)
    startTimes[f] = -1
    if startTime > 0:
        duration = curTime-startTime
        prevDuration = times.get(f, 0)
        times[f] = prevDuration + duration


def showSummary():
    print('Performance Summary')
    print('===================')
    for k in times.keys():
        msg = f'{k}: {times[k]*(10**-9)}s'
        print(msg)


def getFunctionName(name):
    f = str(name) if name != None else str(inspect.stack()[2][3])
    return f
