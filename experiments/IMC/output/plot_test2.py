import matplotlib.pyplot as plot
import numpy as np
import os

if __name__ == '__main__':
    dt = 0.125
    ROI = 0

    col_names = ["pred_state", "pred_stated", "act_state", "act_stated", "loss"]
    col_names2 = [ "Reference", "Referenced", "act_state", "act_stated", "loss", "MI", "FB"]
    dTypes = ["float", "float", "float", "float", "float"]
    dTypes2 = ["float", "float", "float", "float", "float", "float", "float"]
    mydata = np.genfromtxt("testFor.log", delimiter=",", names=col_names, dtype=dTypes)
    mydata2 = np.genfromtxt("testInv.log", delimiter=",", names=col_names2, dtype=dTypes2)

    time = np.linspace(0, mydata["pred_state"].__len__() * dt - dt, mydata["pred_state"].__len__())
    window = mydata["pred_state"].__len__()/100
    #window = 10
    
    figure, axis = plot.subplots(4, 3)
    for i in range(3):
        window = window+window*i*i
        axis[0][i].plot(time, mydata2["Reference"], color = (0,0,0))
        axis[0][i].plot(time, mydata["act_state"] , color = "red")
        axis[0][i].plot(time, mydata["pred_state"], color = "blue")
        axis[0][i].set_ylim(-.1, 1.1)
        axis[0][i].set_xlim(ROI, ROI+window)
        axis[0][i].set_xlabel("Time [s]")
        axis[0][i].grid(True)
        axis[0][i].legend(["Reference", "act_state", "pred_state"])
        axis[0][i].set_ylabel("Position")

        axis[1][i].plot(time, mydata2["Referenced"], color = (0,0,0), linestyle='--')
        axis[1][i].plot(time, mydata["act_stated"] , color = "red", linestyle='--')
        axis[1][i].plot(time, mydata["pred_stated"], color = "blue", linestyle='--')
        axis[1][i].set_ylim(-.1, 1.1)
        axis[1][i].set_xlim(ROI, ROI+window)
        axis[1][i].set_xlabel("Time [s]")
        axis[1][i].grid(True)
        axis[1][i].legend(["Reference", "act_stated", "pred_stated"])
        axis[1][i].set_ylabel("Velocity")

        axis[2][i].plot(time, mydata["loss"], color = "gray")
        axis[2][i].plot(time, mydata2["loss"], color = "gray", linestyle='--')
        axis[2][i].set_xlim(ROI, ROI+window)
        axis[2][i].set_xlabel("Time [s]")
        axis[2][i].set_ylabel("loss")
        axis[2][i].grid(True)
        axis[2][i].legend(["Forward", "Inv"])

        axis[3][i].plot(time, mydata2["MI"], color = "yellow", linestyle='--')
        axis[3][i].plot(time, mydata2["FB"], color = "green", linestyle='--')
        axis[3][i].set_xlim(ROI, ROI+window)
        axis[3][i].set_xlabel("Time [s]")
        axis[3][i].grid(True)
        axis[3][i].set_ylabel("Motor Input")
        #figure.tight_layout()
    figure.set_size_inches(25, 15)
    #figure.set_size_inches(50,30)
    plot.show()
    
    os.system("plot_test1.py 12")