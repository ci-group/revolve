Celery is a task distribution manager. We can start it from this folder, however most
of the times it would be better to start it from the revolve folder.

In Revolve/

Celery worker -A pycelery --loglevel=info -c=n_cores

This will start a celery worker with concurrency n_cores. But it will not do anything
more then starting the worker. After this is done, tasks can be called from other files aslong as this task is imported!

If we call

./revolve.py --celery True --manager pycelery/tasks.py --simulator-cmd=gazebo --n-cores 8

it will start celery for you with 8 workers, and then the manager used is the function run inside of pycelery/tasks.py. Here the experiment should be build and tasks should be used to start gazebo and load robots etc.




			#---------------------# PROBLEMS #--------------------------#

- 	To start gazebo instances from another place, they need the argument settings, these are not
	serializable (yet), but can be serialised by implementing a dictionary.
	
	Solution: Found. Implemented a converter.py file, this file contains args_to_dic to convert
	our arguments to a dictionary, and dic_to_args to convert it back! It also contains args_default if 
	anyone wants to just load the default arguments.


- 	Trying to start a gazebo instance from another place than the first called manager results
	in a RuntimeError: Cannot add child handler, the child watcher does not have a loop attached.

	Solution: Added a childhandler and attached the loop in both the main thread, and in the workers. At 
	the moment is runs fine.
	
- 	Initializing gazebo instances from the main manager works, however if we want other workers 
	to implement robots in these instances, they need the connection object, which is not serializable.
	
	solution: since problem 2 is fixed, this problem is no longer relevant and desirable.
