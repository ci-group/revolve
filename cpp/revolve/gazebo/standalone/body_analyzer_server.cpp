#include "gazebo/common/Exception.hh"
#include "gazebo/util/LogRecord.hh"
#include "gazebo/common/Console.hh"
#include "gazebo/Server.hh"

//////////////////////////////////////////////////
int main(int argc, char **argv)
{
	gazebo::Server *server = NULL;

	try
	{
		// Initialize the informational logger. This will log warnings, and
		// errors.
		gzLogInit("server-", "gzserver.log");

		// Initialize the data logger. This will log state information.
		gazebo::util::LogRecord::Instance()->Init("gzserver");

		server = new gazebo::Server();
		if (!server->ParseArgs(argc, argv))
			return -1;

		server->Run();
		server->Fini();

		delete server;
	}
	catch(gazebo::common::Exception &_e)
	{
		_e.Print();

		server->Fini();
		delete server;
		return -1;
	}

	return 0;
}