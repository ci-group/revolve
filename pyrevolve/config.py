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

        k, v = "--" + arg_line[:split].replace("_", "-"), arg_line[1 + split:]

        # Try to determine if this key is a store constant action, if so
        # return only the key.
        const = False
        for a in self._actions:
            if k in a.option_strings and a.const is not None:
                const = True
                break

        return [k] if const else [k, v]

    @staticmethod
    def record(args, file):
        """
        Takes the result of `parse_args` and writes it back to a file.
        """
        lines = ["{key}={value}\n".format(key=k, value=args.__dict__[k]) for k
                 in sorted(args.__dict__.keys())]
        with open(file, 'w') as configuration_output:
            configuration_output.writelines(lines)


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
    '--manager',
    default=None,
    type=str,
    help="Determine which manager to use. Defaults to no manager."
)

parser.add_argument(
    '--experiment-name',
    default='default_experiment', type=str,
    help="Name of current experiment. A folder with this name will be created. Default to \"default_experiment\"."
)

parser.add_argument(
    '--use-neat',
    default=False, type=str_to_bool,
    help="Use neat full speciation."
)


parser.add_argument(
    '--run',
    default='1', type=str,
    help="Run of repetition of an experiment. Default to \"1\"."
)

parser.add_argument(
    '--test-robot',
    default=None, type=str,
    help="Alternative to --manager. Start a simulation with a single robot instead of running evolution."
         "Loads a yaml robot."
)

parser.add_argument(
    '--test-robot-collision',
    default=None, type=str,
    help="Alternative to --manager. Tests the collision of a single robot. "
         "Loads a yaml robot."
)

parser.add_argument(
    '--simulator-cmd',
    default='gzserver', type=str,
    help="Determine whether to use gzserver or gazebo. Default to \"gzserver\"."
)

parser.add_argument(
    '--n-cores',
    default=1, type=int,
    help="Number of simulators to use at the same time. Default to \"1\"."
)

parser.add_argument(
    '--port-start',
    default=11345, type=int,
    help="Gazebo ports [start_port, start_port + n_cores + n_analyzers]. Default to \"11345\"."
)

parser.add_argument(
    '--run-simulation',
    default=1, type=int,
    help="If gazebo will actually be used. 1 for yes and 0 for no."
)

parser.add_argument(
    '--watch-type',
    default='watch', type=str,
    help="Uae 'watch' for just watching robots, or 'log' watch and log."
)


parser.add_argument(
    '--world',
    default='worlds/plane.world', type=str,
    help="Determine which world gazebo should use."
         "Usefull not only to change the environment, but also the physical properties of the world "
         "and the simulation/real time ratio (you can use the dedicated real time worlds). "
         "Defaults to \"worlds/plane.world\"."
)

parser.add_argument(
    '--z-start',
    default=0.03, type=float,
    help="Position in the z axis where the robot is placed at the beginning of the simulation. "
         "Default \"0.03\"."
)

parser.add_argument(
    '--p-archive',
    default=0.05, type=float,
    help="Probability of adding any new individual to the novelty archive. "
)

parser.add_argument(
    '--k-novelty',
    default=10, type=int,
    help="K nearest neighbors for calculating novelty. "
)

parser.add_argument(
    '--early-death',
    default=False, type=str_to_bool,
    help="If individuals of the offspring can die in the first season. "
)

parser.add_argument(
    '--resimulate',
    default="", type=str,
    help="Generations in which parents should be simulated again to be tested in a new environment. Example: '3 5 8'. And if empty, then None. "
)

parser.add_argument(
    '--evaluation-time',
    default=30, type=float,
    help="In offline evolution, this determines the length of the experiment run."
    # For old_online_fitness:
    #   "The size of the `speed window` for each robot, i.e. the number of "
    #   "past (simulation) seconds over which its speed is evaluated."
)


parser.add_argument(
    '--n-competing-children',
    default=0, type=int,
    help="Number of children to sample when looking for a child close to its parent. If zero, uses stand reproduction."
)

parser.add_argument(
    '--recovery-enabled',
    default=True, type=str_to_bool,
    help="Whether the recovery is enabled (save and load the recovery both). Default \"True\"."
)

parser.add_argument(
    '--export-phenotype',
    default=True, type=str_to_bool,
    help="Exports yamls with the phenotypes. Default \"True\"."
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
    default="output", type=str,
    help="OLD. Directory where robot statistics are written. Default \"output\"."
)

parser.add_argument(
    '--restore-directory',
    default="restore", type=str,
    help="OLD. Explicit subdirectory of the output directory, if a world "
         "state is present in this directory it will be restored. Default \"restore\"."
)

parser.add_argument(
    '--sensor-update-rate',
    default=8, type=int,
    help='The rate at which Gazebo sensors are set to update their values. Default \"8\".'
)

parser.add_argument(
    '--controller-update-rate',
    default=8, type=int,
    help='The rate at which the `RobotController` is requested to update. Default \"8\".'
)

parser.add_argument(
    '--pose-update-frequency',
    default=5, type=int,
    help="The frequency at which the world is requested to send robot pose"
         " updates (in number of times per *simulation* second). Default \"5\"."
)


def make_revolve_config(conf):
    """
    Turns a `tol` config object into a revolve.angle.robogen compatible config
    object.
    """
    conf.enable_wheel_parts = False

    conf.brain_conf = {}
    return conf
