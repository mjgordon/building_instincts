/*
 *	MultiNEATPluginTools.h
 *
 *  Created on: Mar 14, 2015
 *      Author: raimund
 */

#ifndef EC_PLUGIN_TOOLS_H_
#define EC_PLUGIN_TOOLS_H_

#define USE_BOOST_PYTHON
#define BOOST_DISABLE_ASSERTS

#include "simLib.h"
#include "Genome.h"
#include "NeuralNetwork.h"
#include <stdio.h>
#include <stdlib.h>
#include <vector>

void LUA_TRIGGER_BRAIN_CALLBACK(SLuaCallBack* p);
void LUA_INIT_EVAL_CALLBACK(SLuaCallBack* p);
void LUA_SET_FITNESS_CALLBACK(SLuaCallBack* p);
void LUA_END_EVAL_CALLBACK(SLuaCallBack* p);
void LUA_BUILD_BRAIN_CALLBACK(SLuaCallBack* p);


class Bot
{
	const char* c_bot_name;
	int bot_handle;
	int in_clone_group;
	std::string bot_name;
	NEAT::Genome initial_genome;
	NEAT::Genome bot_genome;
	NEAT::NeuralNetwork brain;
	NEAT::Substrate substrate;
	std::vector<int> motor_handles;

public:

	unsigned short int n_NN_outputs;
	unsigned short int n_NN_inputs;

	//CONSTRUCTORS
	Bot(std::string botName);
	Bot();

	//MEMBERS
	void MakeNEATBrain();
    void MakeNEATBrainFromFile(std::string filename);
	void MakeHyperNEATBrain();
	void Move(std::vector<float> NN_to_motors);
	std::vector<double> BrainResponse(std::vector<double> NNinputs);
	void PublishFitnessScore();

	//ACCESS
	int MemberOfGroup();
	int GetHandle();
	NEAT::Genome GetGenome();
	std::string GetName();
	void SetGenome(NEAT::Genome a_genome);
	void SetBotFitness(double a_fitness);
	void SetCloneGroup(int a_cloneGroupContainerIndex);

	//DEBUG
	void report();
};

class CloneGroup
{
	std::string group_name;
	const char* c_group_name;
	int group_handle;
	NEAT::Genome initial_genome;
	NEAT::Genome group_genome;
	std::vector<Bot*> member_bots; //vector of pointers is questionable

public:

	//CONSTRUCTORS
	CloneGroup(std::string groupName);
	CloneGroup();

	//MEMBERS
	void AddMemberBot(Bot* p_clone_bot);
	void PublishFitnessScore();

	//ACCESS
	void SetCGFitness(double fitness);
	void SetGenome(NEAT::Genome genome);
	NEAT::Genome GetGenome();
	int GetHandle();
	std::string GetName();
	std::vector<Bot*> GetMemberBots();
};

void ECAutoRegister(unsigned maxCloneGroups, unsigned maxBots);	// count the bots in the scene, initialize bot objects

bool WaitForMasterStatus(int expected, unsigned timeout); // timeout in seconds

std::vector<std::string> ECGetGenomeFilenamesFromMaster();	// Get String Signals for Genome Filenames from Master and return List of Filenames

std::vector<std::string> ECCreateGenomeFilenames(std::string base, std::string suffix);	// Create Genome Filenames based on Naming Convention (genome_n.mng), n as required for vrep-scene

std::vector<NEAT::Genome> ECLoadGenomes(std::vector<std::string>* p_filenames);			// Load Genome Files, Instantiate Genome Objects

void ECDistributeGenomess(std::vector<NEAT::Genome> genomes);		// Distribute the Genomes to the Objects in the Scene

void ECPublishFitnessAll();


/***************************Plugin Entry Points**************************************/

void ECPluginLoad();				// called when plugin is loaded i.e. when starting a vrep instance, see v_repStart

void ECPluginSimAboutToStart();		// called just before simulation starts, see v_repMessage >> if (message==sim_message_eventcallback_simulationabouttostart)

void ECPluginSimStep();				// called once every pass of vrep main loop, see v_repMessage >> if (message==sim_message_eventcallback_instancepass)

void ECPluginSceneLoaded();

void ECPluginSimFinished();			// called just after the simulation ended

#endif /* EC_PLUGIN_TOOLS_H_ */
