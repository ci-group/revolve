import os

from isaac import manage_isaac
from pyrevolve import parser


def main():
    arguments = parser.parse_args()

    robot_file = "robot.urdf"
    if arguments.test_robot is not None:
        assert os.path.splitext(arguments.test_robot)[-1]=='urdf', "Expected urdf format"
        robot_file = arguments.test_robot

    with open(robot_file, 'r') as robot:
        urdf_string = robot.read()

    manage_isaac.simulator(urdf_string, 30)


if __name__ == '__main__':
    print("STARTING")
    main()
    print("FINISHED")