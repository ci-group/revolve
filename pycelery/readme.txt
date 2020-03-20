Celery is a task distribution manager. We can start it from this folder, however most
of the times it would be better to start it from the revolve folder.

In Revolve/

We can start revolve using celery when you use the next line.

./revolve.py --manager pycelery/manager.py --n-cores 8

it will start the manager, which uses the class CeleryController to control and start celery. The manager
can shutdown, reset, evaluate robots through this CeleryController. It is used as a simulator_queue class.

Use the manager.py file in the pycelery folder as an example to make your own experiment.

# ---------------------------- # CHANGED FILES #----------------------------#
pyrevolve/evolution/population.py           	(Added a celery part to receive data)- old revolve intact
pyrevolve/tol/manage/robotmanager.py					(Added a way to convert a celery message to a robotmanager class)- old revolve intact
cpprevolve/gazebo/plugin/WorldController.cpp 	(Changed the file to retrieve celery messages from the workers.) - OLD REVOLVE NOT INTACT

			#---------------------# PROBLEMS #--------------------------#

-1. Celery is currently using RabbitMQ and RPC (remote procedure call) to handle messages. RPC is dependent on the
network you are connected to. If the network disconnects the experiment stops. The current
solution is rebooting the network and restarting the experiment.

-2. If a robot takes a lot of time, the get request will back off for max 1 second before trying again. However,
this 1 second between get request holds on to long. You will get moments were there is exactly 1 second between
robot results. I am not sure how to get rid of this delay after the that initial robot is evaluated (then the timer should
go back to like 0.01 or something).

-3. If a gazebo instance is running, the robot simulation time is building up. This is normal since robots
are getting more complex over time, however I believe it should decrease and at some point reach a threshold.
It is not memory leaking because the memory usage is not increasing, however the computation time is. A solution is
restarting the simulator per X generations, however I think it should be possible without restarting.

-4. If in any case the experiment is disrupted, and stopped, celery messages can still be in the system. Restarting without removing
these messages will give errors. So before restarting the experiment; celery, gazebo and the messages need to be deleted.
This can be done by the following two commands:
	- $ pkill -9 -f 'celery worker' && pkill -9 -f 'gzserver'
	- $ celery amqp && queue.delete cpp && queue.delete robots
