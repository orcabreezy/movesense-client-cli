import heartpy as hp
import pandas as pd

if __name__ == "__main__":
    df = pd.read_csv("run_24012026.csv")
    data = df[" value"].to_numpy()[1:]
    working_data, measures = hp.process(data[100000:110000], 500.0)
    print(measures["bpm"])
    print(measures["rmssd"])
    plot = hp.plotter(working_data, measures, show=False)
    plot.savefig("plot.pdf")
