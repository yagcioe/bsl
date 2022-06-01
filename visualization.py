
import matplotlib.pyplot as plt
from . import environment as env

from . import util

def scatterplot3d(points, dims):
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.set_xlim(0, dims[0])
    ax.set_ylim(0, dims[1])
    ax.set_zlim(0, dims[2])
    c = listenerSpeakerColors(len(points))

    i = 0
    for p in points:
        ax.scatter(p[0], p[1], p[2], color=c[i])
        i = i+1


def scatterplot2d(points, middle, directivities, dims):
    plot2dPoints(points)
    plt.scatter(middle[0], middle[1], c='#5f59')
    if dims != None:
        plt.xlim(0, dims[0])
        plt.ylim(0, dims[1])


def plotDirectivities(base, middle, baseRefDirs, pos, posDirs, roomCorners):
    def sub(x, y):
        return [x[0]-y[0], x[1]-y[1]]

    arrowLen = 5
    fig = plt.figure(dpi=env.figureDpi)
    plt.gca().set_aspect('equal', adjustable='box')

    a = roomCorners[0]
    b = roomCorners[1]
    c = roomCorners[3]
    d = roomCorners[2]

    plt.arrow(a[0], a[1], sub(b, a)[0], sub(b, a)[1], color='#000',head_width=0,head_length=0)
    plt.arrow(b[0], b[1], sub(c, b)[0], sub(c, b)[1], color='#000',head_width=0,head_length=0)
    plt.arrow(c[0], c[1], sub(d, c)[0], sub(d, c)[1], color='#000',head_width=0,head_length=0)
    plt.arrow(d[0], d[1], sub(a, d)[0], sub(a, d)[1], color='#000',head_width=0,head_length=0)

    plt.scatter(base[0], base[1], c='#55f9')
    plt.scatter(middle[0], middle[1], c='#5f59')
    
    v = util.toVektor(baseRefDirs[0], arrowLen)
    plt.arrow(base[0], base[1], v[0], v[1], color='#5f59')


    for i in range(len(posDirs)):
        v = util.toVektor(posDirs[i][0], arrowLen)
        plt.arrow(base[0], base[1], v[0], v[1], color='#f559')
    
    for i in range(len(pos)):
        plt.scatter(pos[i][0], pos[i][1], c='#f559')

    plt.close()
    return fig


def pd(positions,dirs):
    c= ['g','b','c','r','m','y','k']
    fig = plt.figure()
    plt.gca().set_aspect('equal', adjustable='box')

    for p in positions:
        plt.scatter(p[0], p[1])
    arrowLen = 5
    for i in range(len(dirs)):
        v = util.toVektor(dirs[i][0], arrowLen)
        #  c= '#f559' if i != 0 else '#55ff55'
        plt.arrow(positions[0][0], positions[0][1], v[0], v[1],color = c[i%len(c)])
    return fig
   
    

def plot2dPoints(points):
    x = [points[i][0] for i in range(len(points))]
    y = [points[i][1] for i in range(len(points))]
    c = listenerSpeakerColors(len(points))
    plt.scatter(x, y, c=c)


def listenerSpeakerColors(count: int):
    if count < 1:
        return []
    if count == 1:
        return ['#55F9']
    colors = ['#55F9']
    for i in range(1, count):
        colors.append('#F559')
    return colors



def customPlot(positions, middle, dirs, baseAngle, roomDims):
    positionsC = positions.copy()
    dirs = dirs.copy()
    roomDims = roomDims.copy()
    a = [0, 0, 0]
    b = [roomDims[0], 0, 0]
    c = [0, roomDims[1], 0]
    d = [roomDims[0], roomDims[1], 0]
    roomCorners = [a, b, c, d]

    fig1 = plotDirectivities(positions[0], middle, dirs[0],
                    positions[1:], dirs[1:], roomCorners)

    positions = util.normalizeAllPoints(positions,positionsC[0],baseAngle)
    roomCorners = util.normalizeAllPoints(roomCorners,positionsC[0],baseAngle)
    middle = util.normalizePoint(middle,positionsC[0],baseAngle)

    dirs = util.normalizeAllAngles(dirs,baseAngle)
    fig = plotDirectivities(positions[0], middle, dirs[0],
                      positions[1:], dirs[1:], roomCorners)
    plt.close(fig)
    return fig1,fig


def plotTracks(tracks):
    fig = plt.figure(dpi=env.figureDpi)
    plt.xlabel("Zeit [s]")
    plt.ylabel("Sprecher")
    plt.yticks(ticks=range(len(tracks)))
    colors = ['#F55', '#5F5', '#55F']
    for i in range(len(tracks)):
        for s in tracks[i]:
            c = colors[i % len(colors)]
            plt.arrow(s.startTime, i, s.duration, 0, color=c, width=0.8,head_width=0)
    plt.close(fig)
    return fig
