/**
 * The default Gazebo server provides no easy way of setting
 * the port at which it runs. There is the GAZEBO_MASTER_URI
 * environment variable, but it is overwritten with the
 * default when Gazebo is started. This executable is identical
 * to Gazebo's server, except it overrides the environment
 * variable before starting.
 *
 * @author Elte Hupkes
 */
#include "gazebo/common/Exception.hh"
//#include "gazebo/util/LogRecord.hh"
#include "gazebo/common/Console.hh"
#include "gazebo/Server.hh"

//////////////////////////////////////////////////
int main(int argc, char **argv)
{
	char *analyzerLoaded = getenv("ANALYZER_TOOL");
	if (!analyzerLoaded) {
		std::cerr << "Please run using tools/run-analyzer.sh" << std::endl;
		return -1;
	}

	// Set the port to 11346 rather than 11345
	setenv("GAZEBO_MASTER_URI", "http://localhost:11346", 1);
	gazebo::Server *server = NULL;

	try
	{
		// Initialize the informational logger. This will log warnings, and
		// errors.
		gzLogInit("server-analyzer-", "gzserver_analyzer.log");

		// Initialize the data logger. This will log state information.
//		gazebo::util::LogRecord::Instance()->Init("gzserver");

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