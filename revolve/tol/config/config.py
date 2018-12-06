from __future__ import absolute_import

import argparse


class CustomParser(argparse.ArgumentParser):
    """
    Extends argument parser to add some simple file reading / writing
    functionality.
    """
    def convert_arg_line_to_args(self, arg_line):
        """
        Simple arg line converter that returns `--my-argument value` from
        lines like "my_argument=value"
        :param arg_line:
        :return:
        """
        # Empty or comment line
        if not arg_line or arg_line[0] == "#":
            return []

        split = arg_line.find("=")
        if split < 0:
            return [arg_line]

        k, v = "--"+arg_line[:split].replace("_", "-"), arg_line[1+split:]

        # Try to determine if this key is a store constant action, if so
        # return only the key.
        const = False
        for a in self._actions:
            if k in a.option_strings and a.const is not None:
                const = True
                break

        return [k] if const else [k, v]

    def write_to_file(self, args, file):
        """
        Takes the result of `parse_args` and writes it back
        to a file.
        """
        lines = ["%s=%s\n" % (k, args.__dict__[k]) for k in sorted(args.__dict__.keys())]
        with open(file, 'w') as o:
            o.writelines(lines)


def str_to_bool(v):
    """
    :type v: str
    """
    return v.lower() in ("true", "1")


def str_to_address(v):
    """
    :type v: str
    """
    if not v:
        return None

    host, port = v.split(":", 1)
    return host, int(port)


parser = CustomParser(fromfile_prefix_chars='@')
parser.add_argument(
    '--sensor-update-rate',
    default=8, type=int,
    help='The rate at which Gazebo sensors are set to update their values.'
)

parser.add_argument(
    '--controller-update-rate',
    default=8, type=int,
    help='The rate at which the `RobotController` is requested to update.'
)

parser.add_argument(
    '--visualize-sensors',
    default=False, type=bool,
    help='Visualize sensors (helpful for debugging purposes)'
)

parser.add_argument(
    '--pose-update-frequency',
    default=5, type=int,
    help="The frequency at which the world is requested to send robot pose"
         " updates (in number of times per *simulation* second)."
)

parser.add_argument(
    '--evaluation-time',
    default=12, type=float,
    help="The size of the `speed window` for each robot, i.e. the number of past (simulation) seconds "
         "over which its speed is evaluated. In offline evolution, this determines the length"
         "of the experiment run."
)

parser.add_argument(
    '--min-parts',
    default=3, type=int,
    help="Minimum number of parts in a robot."
)

parser.add_argument(
    '--max-parts',
    default=30, type=int,
    help="Maximum number of parts in a robot."
)

parser.add_argument(
    '--initial-parts-mu',
    default=12, type=int,
    help="Mean part count of generated robots."
)

parser.add_argument(
    '--initial-parts-sigma',
    default=5, type=int,
    help="Standard deviation of part count in generated robots."
)

parser.add_argument(
    '--max-inputs',
    default=10, type=int,
    help="Maximum number of inputs (i.e. sensors) in a robot."
)

parser.add_argument(
    '--max-outputs',
    default=10, type=int,
    help="Maximum number of outputs (i.e. motors) in a robot."
)

parser.add_argument(
    '--enforce-planarity',
    default=True, type=str_to_bool,
    help="Force bricks to be in default orientation and disable parametric bar joint rotation."
)

parser.add_argument(
    '--body-mutation-epsilon',
    default=0.05, type=float,
    help="Mutation epsilon for robot body parameters."
)

parser.add_argument(
    '--brain-mutation-epsilon',
    default=0.1, type=float,
    help="Mutation epsilon for robot neural net parameters."
)

parser.add_argument(
    '--p-duplicate-subtree',
    default=0.1, type=float,
    help="Probability of duplicating a subtree."
)

parser.add_argument(
    '--p-connect-neurons',
    default=0.1, type=float,
    help="Initial connection probability."
)

parser.add_argument(
    '--p-swap-subtree',
    default=0.05, type=float,
    help="Probability of swapping two subtrees."
)

parser.add_argument(
    '--p-delete-subtree',
    default=0.05, type=float,
    help="Probability of deleting a subtree."
)

parser.add_argument(
    '--p-remove-brain-connection',
    default=0.05, type=float,
    help="Probability of removing a neural network connection."
)

parser.add_argument(
    '--p-delete-hidden-neuron',
    default=0.05, type=float,
    help="Probability of deleting a random hidden neuron."
)

parser.add_argument(
    '--world-address',
    default="127.0.0.1:11345", type=str,
    help="Host:port of the simulator."
)

parser.add_argument(
    '--gazebo-cmd',
    default='gzserver', type=str,
    help="Determine wether to use gzserver or gazebo."
)

parser.add_argument(
    '--world',
    default='offline-evolve.world', type=str,
    help="Determine which world to use."
)

parser.add_argument(
    '--manager',
    default='offline_evolve.py', type=str,
    help="Determine which manager to use."
)

parser.add_argument(
    '--robot-name',
    default="spider", type=str,
    help="Name of robot."
)

parser.add_argument(
    '--experiment-round',
    default="1", type=str,
    help="Round of robot experiment."
)

parser.add_argument(
    '--brain-conf-path',
    default="rlpower.cfg", type=str,
    help="Path to brain configuration."
)

parser.add_argument(
    '--load-controller',
    default=None, type=str,
    help="Path to controller data."
)

# Directory where robot information will be written. The system writes
# two main CSV files:
# - The `robots.csv` file containing all the basic robot information, one line
#   per robot, in the format
#   id,parent1,parent2
# - The `poses.csv` file containing each robot pose through time, in the format
#   id,sim_time_sec,sim_time_nsec,x,y,z
#
# Additionally, the `Robot` protobuf message for each bot is written to
# a file called `robot_[ID].pb` when the robot is first registered.
#
# The files are written to a new YYYYMMDDHHIISS directory within the
# specified output directory, unless a subdirectory is explicitly
# provided with `--restore-directory`
parser.add_argument(
    '--output-directory',
    default=None, type=str,
    help="Directory where robot statistics are written."
)

parser.add_argument(
    '--restore-directory',
    default=None, type=str,
    help="Explicit subdirectory of the output directory, if a world "
         "state is present in this directory it will be restored."
)

parser.add_argument(
    '--disable-sensors',
    default=False, type=str_to_bool,
    help="Disables all sensors - overriding specific sensor settings. In practice "
         "this means that the core component is created without an IMU sensor, whereas "
         "the other sensor parts are not enabled at all."
)

parser.add_argument(
    '--enable-touch-sensor',
    default=True, type=str_to_bool,
    help="Enable / disable the touch sensor in robots."
)

parser.add_argument(
    '--enable-light-sensor',
    default=False, type=str_to_bool,
    help="Enable / disable the light sensor in robots."
)

parser.add_argument(
    '--warmup-time',
    default=0, type=float,
    help="The number of seconds the robot is initially ignored, allows it to e.g. topple over"
         " when put down without that being counted as movement. Especially helps when dropping"
         " robots from the sky at the start."
)

parser.add_argument(
    '--fitness-size-factor',
    default=0, type=float,
    help="Multiplication factor of robot size in the fitness function. Note that this"
         " needs to be negative to discount size."
)

parser.add_argument(
    '--fitness-velocity-factor',
    default=1.0, type=float,
    help="Multiplication factor of robot velocity in the fitness function."
)

parser.add_argument(
    '--fitness-displacement-factor',
    default=5.0, type=float,
    help="Multiplication factor of robot displacement velocity (= velocity in a straight line "
         " in the fitness function."
)

parser.add_argument(
    '--fitness-size-discount',
    default=0, type=float,
    help="Another possible way of discounting robot size, multiplies the previously calculated"
         " fitness by (1 - d * size) where `d` is this discount factor."
)

parser.add_argument(
    '--fitness-limit',
    default=1.0, type=float,
    help="Minimum fitness value that is considered unrealistic and should probably be attributed"
         " to a simulator instability. A fitness of zero is returned in this case."
)

parser.add_argument(
    '--tournament-size',
    default=4, type=int,
    help="The size of the random tournament used for parent selection, if"
         " selection is enabled. When individuals are chosen for reproduction,"
         " this number of possible parents is randomly sampled from the population,"
         " and out of these the best is chosen. A larger number here means higher"
         " selection pressure but less selection variance and vice versa."
)

parser.add_argument(
    '--max-mating-attempts',
    default=5, type=int,
    help="Maximum number of mating attempts between two parents."
)


parser.add_argument(
    '--world-step-size',
    default=0.003, type=float,
    help="The physics step size configured in the simulation world file. This needs to match"
         " in order to configure some physics parameters."
)


def make_revolve_config(conf):
    """
    Turns a `tol` config object into a revolve.angle.robogen compatible config
    object.
    """
    conf.enable_wheel_parts = False
    return conf
