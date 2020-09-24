import math

battery_path = "data/battery/1/data_fullevolution/battery"
fitness_path = "data/battery/1/data_fullevolution/fitness"
phenotypes_path = "data/battery/1/data_fullevolution/phenotypes"

battery_usages = []

# open all files in folder
import glob
import os
import yaml
filenames = glob.glob(os.path.join(battery_path, '*.txt'))
indexes = range(len(filenames))

def read_files(path):
    values = []
    for filename in glob.glob(os.path.join(path, '*.txt')):
      with open(filename, 'r') as f:
          value = f.readline()
          values.append(float(value if value != 'None' else 0.0))
    return values

def read_yaml_files(path):
    values = []
    index = 0
    for filename in glob.glob(os.path.join(path, '*.yaml')):
        with open(filename, 'r') as f:
            values.append(count_robot_size(f))
        if index % 100:
            print(index)
        index += 1
    return values


def count_robot_size(stream) -> int:
    number_of_elements = 0
    try:
        body = yaml.safe_load(stream)['body']
        text = yaml.dump(body)
        number_of_elements = text.count("id:")
    except yaml.YAMLError as exc:
        print(exc)
    return number_of_elements



battery_values = read_files(battery_path)
print("read battery")
fitness_values = read_files(fitness_path)
print("read fitness")
robot_size_values = read_yaml_files(phenotypes_path)
print("read robot yamls")

import matplotlib.pyplot as plt

plt.title("Energy usage for each robot generated.")

plt.xlabel("Robot index")
plt.ylabel("Amount of energy expanded during simulation")
plt.show()

plt.title("Fitness for each robot generated.")

plt.xlabel("Robot index")
plt.ylabel("Fitness")
plt.show()

plt.title("Robot size for each robot generated.")

plt.xlabel("Robot index")
plt.ylabel("Robot Size")
plt.show()

from mpl_toolkits.axes_grid1 import host_subplot
import mpl_toolkits.axisartist as AA
import matplotlib.pyplot as plt

host = host_subplot(111, axes_class=AA.Axes)
plt.subplots_adjust(right=0.75)

par1 = host.twinx()
par2 = host.twinx()

offset = 60
new_fixed_axis = par2.get_grid_helper().new_fixed_axis
par2.axis["right"] = new_fixed_axis(loc="right",
                                    axes=par2,
                                    offset=(offset, 0))

par2.axis["right"].toggle(all=True)

host.set_xlabel("Robot Index")
host.set_ylabel("Battery")
par1.set_ylabel("Fitness")
par2.set_ylabel("Size")

p1, = host.plot(indexes, battery_values, label="Battery")
p2, = par1.plot(indexes, fitness_values, label="Fitness")
p3, = par2.plot(indexes, robot_size_values, label="Size")

host.legend()

host.axis["left"].label.set_color(p1.get_color())
par1.axis["right"].label.set_color(p2.get_color())
par2.axis["right"].label.set_color(p3.get_color())

plt.draw()
plt.show()