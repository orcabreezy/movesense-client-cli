import numpy as np
import pyqtgraph as pg
from PyQt5 import QtCore

if __name__ == "__main__":
    app = pg.mkQApp("RealTimeAccel")
    plot = pg.plot(title="accelerometer data")
    curve = plot.plot(pen="y")

    data = np.random.normal(size=100)

    def update():
        global data
        new_data = np.random.normal()
        data = np.roll(data, -1)
        data[-1] = new_data
        curve.setData(data)

    timer = QtCore.QTimer()
    timer.timeout.connect(update)
    timer.start(40)

    app.exec_()
