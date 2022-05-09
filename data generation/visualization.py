
import matplotlib.pyplot as plt
import environment as env

import util

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
    plt.figure(figsize=(10,10))
    plt.xlim(-env.room_dim_ranges[0][1], env.room_dim_ranges[0][1])
    plt.ylim(-env.room_dim_ranges[1][1], env.room_dim_ranges[1][1])

    a = roomCorners[0]
    b = roomCorners[1]
    c = roomCorners[3]
    d = roomCorners[2]

    plt.arrow(a[0], a[1], sub(b, a)[0], sub(b, a)[1], color='#000')
    plt.arrow(b[0], b[1], sub(c, b)[0], sub(c, b)[1], color='#000')
    plt.arrow(c[0], c[1], sub(d, c)[0], sub(d, c)[1], color='#000')
    plt.arrow(d[0], d[1], sub(a, d)[0], sub(a, d)[1], color='#000')
    plt.gca().set_aspect('equal', adjustable='box')

    plt.scatter(base[0], base[1], c='#55f9')
    plt.scatter(middle[0], middle[1], c='#5f59')
    
    v = util.toVektor(baseRefDirs[0], arrowLen)
    plt.arrow(base[0], base[1], v[0], v[1], color='#5f59')


    for i in range(len(posDirs)):
        v = util.toVektor(posDirs[i][0], arrowLen)
        plt.arrow(base[0], base[1], v[0], v[1], color='#f559')
        plt.scatter(pos[i][0], pos[i][1], c='#f559')


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
    plt.figure(figsize=(10,10))
    positions = positions.copy()
    dirs = dirs.copy()
    roomDims = roomDims.copy()
    a = [0, 0, 0]
    b = [roomDims[0], 0, 0]
    c = [0, roomDims[1], 0]
    d = [roomDims[0], roomDims[1], 0]
    roomCorners = [a, b, c, d]

    positions = [util.rotateAroundPoint(v, positions[0], -baseAngle)
                 for v in positions]
    roomCorners = [util.rotateAroundPoint(v, positions[0], -baseAngle)
                   for v in roomCorners]
    dirs = [[d[0]-baseAngle, d[1]] for d in dirs]
    middle = util.rotateAroundPoint(middle,positions[0],-baseAngle)
    plotDirectivities(positions[0], middle, dirs[0],
                      positions[1:], dirs[1:], roomCorners)
    fig = plt.gcf()
    if(env.visualize):
        plt.show()
    else:
        plt.close()
    return fig


def plotTracks(tracks):
    plt.clf()
    colors = ['#F55', '#5F5', '#55F']
    for i in range(len(tracks)):
        for s in tracks[i]:
            c = colors[i % len(colors)]
            plt.arrow(s.startTime, i+0.4, s.duration, 0, color=c, width=0.8,head_width=0)
    plt.title('Speaker Tracks')
    plt.show()
