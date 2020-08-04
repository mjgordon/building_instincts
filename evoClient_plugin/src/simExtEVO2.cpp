/*
 * v_repExtNEAT.cpp
 *
 *  Created on: Mar 2, 2015
 *      Author: raimund
 */

// Copyright 2006-2014 Coppelia Robotics GmbH. All rights reserved.
// This file was automatically created for V-REP release V3.2.0 on Feb. 3rd 2015


#include "simLib.h"
#include "simExtEVO2.h"
#include <iostream>
#include <vector>
#include "EvoClientPluginTools.h"


#ifdef _WIN32
	#include <shlwapi.h>
	#pragma comment(lib, "Shlwapi.lib")
#endif /* _WIN32 */

#if defined (__linux) || defined (__APPLE__)
	#include <unistd.h>
	#include <string.h>
	#define _stricmp(x,y) strcasecmp(x,y)
#endif

#define PLUGIN_VERSION 1

LIBRARY simLib; // the V-REP library that we will dynamically load and bind

#define CONCAT(x,y,z) x y z
#define strConCat(x,y,z)	CONCAT(x,y,z)

/***********************/

std::vector<Bot> botContainer ;		// needs to be accessed by callback function, hence global
std::vector<CloneGroup> cloneGroupContainer;
std::vector<std::string> genomeFilenamesContainer;
unsigned sim_start_counter;
bool debug = true;

// This is the plugin start routine (called just once, just after the plugin was loaded):
SIM_DLLEXPORT unsigned char simStart(void* reservedPointer,int reservedInt)
{
	// Dynamically load and bind V-REP functions:
	// ******************************************
	// 1. Figure out this plugin's directory:
	char curDirAndFile[1024];
#ifdef _WIN32
	GetModuleFileName(NULL,curDirAndFile,1023);
	PathRemoveFileSpec(curDirAndFile);
#elif defined (__linux) || defined (__APPLE__)
	getcwd(curDirAndFile, sizeof(curDirAndFile));
#endif
	std::string currentDirAndPath(curDirAndFile);


	// 2. Append the V-REP library's name:
	std::string temp(currentDirAndPath);
#ifdef _WIN32
	temp+="\\v_rep.dll";
#elif defined (__linux)
	temp+="/libcoppeliaSim.so";
#elif defined (__APPLE__)
	temp+="/libv_rep.dylib";
#endif /* __linux || __APPLE__ */

	// 3. Load the V-REP library:
	simLib=loadSimLibrary(temp.c_str());
	if (simLib==NULL)
	{
		std::cout << "Error, could not find or correctly load the V-REP library. Cannot start 'PluginSkeleton' plugin.\n";
		return(0); // Means error, V-REP will unload this plugin
	}
	if (getSimProcAddresses(simLib)==0)
	{
		std::cout << "Error, could not find all required functions in the V-REP library. Cannot start 'PluginSkeleton' plugin.\n";
		unloadSimLibrary(simLib);
		return(0); // Means error, V-REP will unload this plugin
	}
	// ******************************************
	// Check the version of V-REP:
	// ******************************************
	int simVer;
	simGetIntegerParameter(sim_intparam_program_version,&simVer);
	if (simVer<20604) // if V-REP version is smaller than 2.06.04
	{
		std::cout << "Sorry, your V-REP copy is somewhat old. Cannot start 'PluginSkeleton' plugin.\n";
		unloadSimLibrary(simLib);
		return(0); // Means error, V-REP will unload this plugin
	}

	// ******************************************
	// Register Lua commands:
	// ******************************************
	// Input Arguments of the 'simExtNEAT_triggerbrain' custom Lua command: a table of floats
	int inArgs_triggerBrain[]={1,sim_lua_arg_float|sim_lua_arg_table}; // one argument: table of float NN_in_data
	int inArgs_initEvoClient[]={0}; // No Arguments
	int inArgs_setFitness[]={1, sim_lua_arg_float};
	int inArgs_endEval[]={0};
    int inArgs_buildBrain[]={1, sim_lua_arg_string};

	// Return value can change on the fly, so no need to specify them here, except for the calltip.
	// Now register the callbacks:
	simRegisterCustomLuaFunction("simExtEVO_triggerBrain",strConCat("table brain_response=","simExtEVO_triggerBrain","(table float NN_in_data)"), inArgs_triggerBrain,LUA_TRIGGER_BRAIN_CALLBACK);
	simRegisterCustomLuaFunction("simExtEVO_initEvaluation","simExtEVO_initEvaluation()",inArgs_initEvoClient,LUA_INIT_EVAL_CALLBACK);
	simRegisterCustomLuaFunction("simExtEVO_setFitness","simExtEVO_setFitness(float fitness)",inArgs_setFitness,LUA_SET_FITNESS_CALLBACK);
	simRegisterCustomLuaFunction("simExtEVO_endEvaluation", "simExtEVO_endEvaluation()", inArgs_endEval, LUA_END_EVAL_CALLBACK);
    simRegisterCustomLuaFunction("simExtEVO_buildBrain", "simExtEVO_buildBrain(string genome_filename)", inArgs_buildBrain, LUA_BUILD_BRAIN_CALLBACK);
	// ******************************************


	// **************
	ECPluginLoad();
	// **************

	return(PLUGIN_VERSION); // initialization went fine, we return the version number of this plugin (can be queried with simGetModuleName)
}

// This is the plugin end routine (called just once, when V-REP is ending, i.e. releasing this plugin):
SIM_DLLEXPORT void simEnd()
{
	// Here you could handle various clean-up tasks

	unloadSimLibrary(simLib); // release the library
}

// This is the plugin messaging routine (i.e. V-REP calls this function very often, with various messages):
SIM_DLLEXPORT void* v_repMessage(int message,int* auxiliaryData,void* customData,int* replyData)
{ // This is called quite often. Just watch out for messages/events you want to handle
	// Keep following 5 lines at the beginning and unchanged:
	static bool refreshDlgFlag=true;
	int errorModeSaved;
	simGetIntegerParameter(sim_intparam_error_report_mode,&errorModeSaved);
	simSetIntegerParameter(sim_intparam_error_report_mode,sim_api_errormessage_ignore);
	void* retVal=nullptr;

	// Here we can intercept many messages from V-REP (actually callbacks). Only the most important messages are listed here.
	// For a complete list of messages that you can intercept/react with, search for "sim_message_eventcallback"-type constants
	// in the V-REP user manual.

	if (message==sim_message_eventcallback_refreshdialogs)
		refreshDlgFlag=true; // V-REP dialogs were refreshed. Maybe a good idea to refresh this plugin's dialog too

	if (message==sim_message_eventcallback_menuitemselected)
	{ // A custom menu bar entry was selected..
		// here you could make a plugin's main dialog visible/invisible
	}

	if (message==sim_message_eventcallback_instancepass)
	{	// This message is sent each time the scene was rendered (well, shortly after) (very often)
		// It is important to always correctly react to events in V-REP. This message is the most convenient way to do so:

		int flags=auxiliaryData[0];
		bool sceneContentChanged=((flags&(1+2+4+8+16+32+64+256))!=0); // object erased, created, model or scene loaded, und/redo called, instance switched, or object scaled since last sim_message_eventcallback_instancepass message
		bool instanceSwitched=((flags&64)!=0);

		//******************
		ECPluginSimStep();
		//******************

		if (instanceSwitched)
		{
			// React to an instance switch here!!
		}

		if (sceneContentChanged)
		{ // we actualize plugin objects for changes in the scene

			//...

			refreshDlgFlag=true; // always a good idea to trigger a refresh of this plugin's dialog here
		}


	}

	if (message==sim_message_eventcallback_mainscriptabouttobecalled)
	{ // The main script is about to be run (only called while a simulation is running (and not paused!))

	}

	if (message==sim_message_eventcallback_simulationabouttostart)
	{ // Simulation is about to start

		//******************
		ECPluginSimAboutToStart();
		//******************

	}

	if (message==sim_message_eventcallback_sceneloaded)
	{
		//******************
		ECPluginSceneLoaded();
		//******************

	}


	if (message==sim_message_eventcallback_simulationended)
	{
		//******************
		ECPluginSimFinished();
		//******************
	}

	if (message==sim_message_eventcallback_moduleopen)
	{ // A script called simOpenModule (by default the main script). Is only called during simulation.
		{
			// we arrive here only at the beginning of a simulation
		}
	}

	if (message==sim_message_eventcallback_modulehandle)
	{ // A script called simHandleModule (by default the main script). Is only called during simulation.
		if ( (customData==nullptr)||(_stricmp("PluginSkeleton",(char*)customData)==0) ) // is the command also meant for this plugin?
		{
			// we arrive here only while a simulation is running
		}
	}

	if (message==sim_message_eventcallback_moduleclose)
	{ // A script called simCloseModule (by default the main script). Is only called during simulation.
		if ( (customData==nullptr)||(_stricmp("PluginSkeleton",(char*)customData)==0) ) // is the command also meant for this plugin?
		{
			// we arrive here only at the end of a simulation
		}
	}

	if (message==sim_message_eventcallback_instanceswitch)
	{ // Here the user switched the scene. React to this message in a similar way as you would react to a full
	  // scene content change. In this plugin example, we react to an instance switch by reacting to the
	  // sim_message_eventcallback_instancepass message and checking the bit 6 (64) of the auxiliaryData[0]
	  // (see here above)

	}

	if (message==sim_message_eventcallback_broadcast)
	{ // Here we have a plugin that is broadcasting data (the broadcaster will also receive this data!)

	}

	if (message==sim_message_eventcallback_scenesave)
	{ // The scene is about to be saved. If required do some processing here (e.g. add custom scene data to be serialized with the scene)

	}

	// You can add many more messages to handle here

	if ((message==sim_message_eventcallback_guipass)&&refreshDlgFlag)
	{ // handle refresh of the plugin's dialogs
		// ...
		refreshDlgFlag=false;
	}

	// Keep following unchanged:
	simSetIntegerParameter(sim_intparam_error_report_mode,errorModeSaved); // restore previous settings
	return(retVal);
}

