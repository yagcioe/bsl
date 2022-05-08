import math
import numpy as np


def norm2(x):
    n = np.sum(list(map(lambda y: y**2, x)))
    return n


def distance(x, y):
    v = [x[i]-y[i] for i in range(len(x))]
    return norm2(v)


def avg(x):
    return sum(x)/len(x)


def toVektor(angle, len):
    return [np.round(len*math.cos(angle), 15), np.round(len*math.sin(angle), 15)]

# von a nach b in deg


def toAngle(a, b):

    deltaY = b[1] - a[1]
    deltaX = b[0] - a[0]
    return math.atan2(deltaY, deltaX)


def rotationMatrix(angle):
    return np.array([[math.cos(angle), -math.sin(angle)],
                     [math.sin(angle), math.cos(angle)]],)


def rotateAroundPoint(v, base, angle):
    x = np.subtract(v, base)
    x = list(np.dot(rotationMatrix(angle), x[:2]))
    x.append(v[2])
    x = np.add(x, base)
    return x.tolist()


def boundAngle(angle):
    while(angle < -math.pi):
        angle += math.pi
    while(angle > math.pi):
        angle = angle-math.pi
    return angle