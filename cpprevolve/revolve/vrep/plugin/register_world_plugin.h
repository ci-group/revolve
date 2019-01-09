#ifdef _WIN32
	#define VREP_DLLEXPORT extern "C" __declspec(dllexport)
#else
	#define VREP_DLLEXPORT extern "C"
#endif // _WIN32

// The 3 required entry points of the plugin:
VREP_DLLEXPORT unsigned char v_repStart(void* reservedPointer,int reservedInt);
VREP_DLLEXPORT void v_repEnd();
VREP_DLLEXPORT void* v_repMessage(int message, int* auxiliaryData, void* customData, int* replyData);

