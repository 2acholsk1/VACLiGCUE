import pandas as pd

df = pd.read_csv("07_loop/drone_car.csv")

df["DroneAltitude"] = df["DroneAltitude"] + 100

df.to_csv("07_loop/drone_car.csv", index=False)
