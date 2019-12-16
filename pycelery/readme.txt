Celery is a task distribution manager. We can start it from this folder, however most
of the times it would be better to start it from the revolve folder.

In Revolve/

Celery multi worker1 worker2 -A pycelery --loglevel=info -c=n_cores

This will start a celery worker with concurrency n_cores. But it will not do anything
more then starting the worker. After this is done, tasks can be called from other files aslong as this task is imported!






			#---------------------# PROBLEMS #--------------------------#

- 	To start gazebo instances from another place, they need the argument settings, these are not
	serializable (yet), but can be serialised by implementing a dictionary.
	Solution: Found. Implemented a converter.py file, this file contains args_to_dic to convert
	our arguments to a dictionary, and dic_to_arg to convert it back!

- 	Trying to start a gazebo instance from another place than the first called manager results
	in a RuntimeError: Cannot add child handler, the child watcher does not have a loop attached.
	Solution: Find a way to add the child handler, or carry the loop into the main manager.

- 	Initializing gazebo instances from the main manager works, however if we want other workers 
	to implement robots in these instances, they need the connection object, which is not serializable.
	Solution: not yet found
