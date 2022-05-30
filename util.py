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
    x = np.add(x, base[:2]).tolist()
    x.append(v[2])
    return x


def translate(point, translation, positve=False):
    trans =  [point[i]+translation[i] for i in range(2)]if positve else [point[i]-translation[i] for i in range(2)]
    if len(point) == 3:
        trans.append(point[2])
    return trans

def translateAngle(x, d, theta):
    v = toVektor(theta,d)
    v.append(0)
    return translate(x,v,True)

def boundAngle(angle, twoPi=False):
    bound = 2*math.pi if twoPi else math.pi
    while(angle < bound-2*math.pi):
        angle += 2*math.pi
    while(angle > bound):
        angle = angle-2*math.pi
    return angle

def azimuth(angle):
    # weird but works in python 3.9 and python 3.10
    if str(type(angle[0])).lower() == "<class 'list'>":
        return [a[0] for a in angle]
    return angle[0]


def join(a, b):
    c = []
    c.extend(a)
    c.extend(b)
    return c


def addColat(angle):
    return [angle, math.pi/2]


def normalizePoint(p, trans, angle):
    v = rotateAroundPoint(p, trans, -angle)
    v = translate(v, trans)
    return v


def normalizeAllPoints(list, trans, angle):
    return [normalizePoint(p, trans, angle) for p in list]


def normalizeAngle(angle, baseAngle):
    return [boundAngle(angle[0]-baseAngle), angle[1]]


def normalizeAllAngles(list, baseAngle):
    return [normalizeAngle(angle, baseAngle) for angle in list]
