/*
 * MultiNEATPluginTools.cpp
 *
 *  Created on: Mar 14, 2015
 *      Author: raimund
 */


#include "EvoClientPluginTools.h"
#include <cmath>
#define PLUGIN_MESSAGE_PREFIX plugin_message_prefix<<"client"<<std::to_string(clientID)<<": "

// Globals
extern std::vector<Bot> botContainer;
extern std::vector<CloneGroup> cloneGroupContainer;
extern std::vector<std::string> genomeFilenamesContainer;
std::string plugin_message_prefix = "evoNET ";  //used in terminal output
simInt clientID = -1;
//DEBUG
extern unsigned sim_start_counter;

/* TODO:
 * RegisterCloneGroup and RegisterBot LUA functions
 * change simSetLastError to simAddLog
 *
 * OLD:
 * assertions
 * Superclass for Bots and CloneGroups
 * HyperNEAT
 * order the correct amount of Genomes from the Evo-Master
 * common notation for variables
 *
 */

//************************BOT CLASS******************************//


Bot::Bot(std::string botName) //constructor
{
	n_NN_outputs = 0;
	n_NN_inputs = 0;
	bot_name = botName;
	initial_genome = NEAT::Genome();
	bot_genome = initial_genome;
	c_bot_name = botName.c_str();
	bot_handle = simGetObjectHandle(c_bot_name);
	in_clone_group = -1; // not part of a group yet
}

void Bot::MakeNEATBrain()
{
	bot_genome.BuildPhenotype(brain);
	n_NN_inputs = brain.m_num_inputs;
	n_NN_outputs = brain.m_num_outputs;
}

void Bot::MakeNEATBrainFromFile(std::string filename)
{
    std::cout << PLUGIN_MESSAGE_PREFIX << "here4" << std::endl;
    NEAT::Genome loaded_genome(filename.c_str());
    std::cout << PLUGIN_MESSAGE_PREFIX << "here5" << std::endl;
    loaded_genome.BuildPhenotype(brain);
    bot_genome = loaded_genome;
    std::cout << PLUGIN_MESSAGE_PREFIX << "here6" << std::endl;
    n_NN_inputs = brain.m_num_inputs;
    n_NN_outputs = brain.m_num_outputs;
}

void Bot::MakeHyperNEATBrain()
{
	//TODO
	bot_genome.BuildHyperNEATPhenotype(brain, substrate);
}

void Bot::SetBotFitness(double a_fitness)
{
	bot_genome.SetFitness(a_fitness);
	bot_genome.SetEvaluated();
}

void Bot::PublishFitnessScore()
{
	std::string fitness_signal_name;
	fitness_signal_name = "FitnessScore_";
	fitness_signal_name.append(std::to_string(bot_genome.GetID()));
	const char* cstr_fitness_signal_name = fitness_signal_name.c_str();
	double score = bot_genome.GetFitness();
	if (bot_genome.m_Evaluated == true)
	{
		simSetFloatSignal(cstr_fitness_signal_name, score);
		//std::cout << "published score" << cstr_fitness_signal_name << std::endl;
	}
	else
	{
	simSetFloatSignal(cstr_fitness_signal_name, -1.0);
	}
}

int Bot::GetHandle()
{
	return bot_handle;
}

std::string Bot::GetName()
{
	return bot_name;
}

int Bot::MemberOfGroup()
{
	return in_clone_group;
}

void Bot::SetGenome(NEAT::Genome a_genome)
{
	bot_genome = a_genome;

}

void Bot::SetCloneGroup(int a_cloneGroupContainerIndex)
{
	in_clone_group = a_cloneGroupContainerIndex;
}

void Bot::report()
{
	std::cout << PLUGIN_MESSAGE_PREFIX << std::endl
			  << "     " << bot_name << std::endl
			  << "     handle: " << bot_handle << std::endl
			  << "     NN inputs: " << n_NN_inputs << std::endl
			  << "     NN outputs: " << n_NN_outputs << std::endl
			  << "     NN based on Genome: " << bot_genome.GetID() << std::endl;
	if (in_clone_group != -1)
	std::cout << "     member of " << cloneGroupContainer[in_clone_group].GetName() << std::endl;
}

std::vector<double> Bot::BrainResponse(std::vector<double> NNinputs)
{
	brain.Input(NNinputs);
	std::vector<double> NN_output;
	brain.ActivateFast(); // uses unsigned sigmoid in all neurons
	//brain.Activate
	//brain.ActivateLeaky(double step);
	NN_output = brain.Output();
	return NN_output;
}

NEAT::Genome Bot::GetGenome()
{
	return bot_genome;
}


//*********************CloneGroup Class***************************//

CloneGroup::CloneGroup(std::string groupName)
{
	group_name = groupName;
	c_group_name = groupName.c_str();
	group_handle = simGetObjectHandle(c_group_name);
	initial_genome = NEAT::Genome();
	group_genome = initial_genome;
}


void CloneGroup::AddMemberBot(Bot* p_clone_bot)
{
	member_bots.push_back(p_clone_bot);
}

void CloneGroup::SetCGFitness(double fitness)
{
	group_genome.SetFitness(fitness);
	group_genome.SetEvaluated();
}

void CloneGroup::SetGenome(NEAT::Genome genome)
{
	group_genome = genome;
}

void CloneGroup::PublishFitnessScore()
{
	std::string fitness_signal_name;
	fitness_signal_name = "FitnessScore_";
	fitness_signal_name.append(std::to_string(group_genome.GetID()));
	const char* cstr_fitness_signal_name = fitness_signal_name.c_str();
	double score = group_genome.GetFitness();
	if (group_genome.m_Evaluated == true) simSetFloatSignal(cstr_fitness_signal_name, score);
	else simSetFloatSignal(cstr_fitness_signal_name, -1.0);
}

NEAT::Genome CloneGroup::GetGenome()
{
	return group_genome;
}

int CloneGroup::GetHandle()
{
	return group_handle;
}
std::string CloneGroup::GetName()
{
	return group_name;
}
std::vector<Bot*> CloneGroup::GetMemberBots()
{
	return member_bots;
}

std::tuple<int, int> ECIdentifyCaller(int* p_caller_handle)
{
    // Search for the caller in Bots and CloneGroups.
    // return tuple:
    // int: -1 for not found, 0 for CloneGroup, 1 for Bot
    // int: caller_ID
    int caller_handle = *p_caller_handle;
    bool found = false;
    int caller_ID;
    int caller_type = -1;
    for (unsigned i=0; i<cloneGroupContainer.size(); i++)
    {
        if (cloneGroupContainer[i].GetHandle() == caller_handle)
        {
            caller_ID = i;
            found = true;
            caller_type = 0;
            break;
        }
    }
    if (found == false)
    {
        for (unsigned i=0; i<botContainer.size(); i++)
        {
            if (botContainer[i].GetHandle() == caller_handle)
            {
                caller_ID = i;
                found = true;
                caller_type = 1;
                break;
            }
        }
    }
    return std::make_tuple(caller_type, caller_ID);
}

void ECAutoRegister(unsigned maxCloneGroups, unsigned maxBots)
{
	////////////////////////////////////////////////////
	// Scans the Scene for Objects that correspond to //
	// the naming convention for Bots and CloneGroups //
	////////////////////////////////////////////////////

	// start with CloneGroups
	int numberSuffix = 0;
	int count = 0;
	bool first = true;
	bool found = true;
	cloneGroupContainer.clear();
	std::string cgNameStandard("CloneGroup");
	const char* c_str_thisCloneGroupName;

	while (found == true)
	{
		count++;
	    std::string thisCloneGroupName;
		if (first == true)
		{
			thisCloneGroupName = cgNameStandard; // the first name to look for is just "CloneGroup"
		}
		else{
			thisCloneGroupName = cgNameStandard; // construct the other names:
			thisCloneGroupName.append("#");
			thisCloneGroupName.append(std::to_string(numberSuffix));
			numberSuffix++;
		}
		c_str_thisCloneGroupName = thisCloneGroupName.c_str();
		if (simGetObjectHandle(c_str_thisCloneGroupName)!= -1) // see if name exists in the vrep scene
		{
			CloneGroup newCloneGroup(thisCloneGroupName);
			cloneGroupContainer.push_back(newCloneGroup);
		}
		else
        {
		    found = false;
            std::string msg = std::to_string(botContainer.size()) + " CloneGroups detected";
            simAddLog("EVO2: ",sim_verbosity_errors, msg.c_str());
        }
		first = false;
	}
	if (cloneGroupContainer.size() == 0) {std::cout << PLUGIN_MESSAGE_PREFIX << "no CloneGroup found" << std::endl;}
	else {std::cout << PLUGIN_MESSAGE_PREFIX << "found " << cloneGroupContainer.size() << " CloneGroup(s)" << std::endl;}

	// now Bots
	botContainer.clear();
	std::string botNameStandard("Bot");
	const char* c_str_thisBotName;
	first = true;
	found = true;
	numberSuffix = 0;
    while (found == true)
	{
		count++;
        std::string thisBotName;
		if (first == true)
		{
			thisBotName = botNameStandard;
		}
		else
		{
			thisBotName = botNameStandard;
			thisBotName.append("#");
			thisBotName.append(std::to_string(numberSuffix));
			numberSuffix++;
		}
		c_str_thisBotName = thisBotName.c_str();
		if (simGetObjectHandle(c_str_thisBotName)!= -1)
		{
			Bot newBot(thisBotName);
			botContainer.push_back(newBot);
			simInt parent = simGetObjectParent(newBot.GetHandle());
			if (parent != -1)
			{
				for (int i=0; i<cloneGroupContainer.size(); i++)
				{
					if (parent == cloneGroupContainer[i].GetHandle())
					{
						cloneGroupContainer[i].AddMemberBot(&botContainer.back());
						botContainer.back().SetCloneGroup(i);
					}
				}
			}
		}
        else
        {
            found = false;
            std::string msg = std::to_string(botContainer.size()) + " Bots detected";
            simAddLog("EVO2: ",sim_verbosity_errors, msg.c_str());
        }
		first = false;
	}
	if (botContainer.size() == 0) {std::cout << PLUGIN_MESSAGE_PREFIX << "no Bots found" << std::endl;}
	else {std::cout << PLUGIN_MESSAGE_PREFIX << "found " << botContainer.size() << " Bot(s)" << std::endl;}
}

bool WaitForMasterStatus(int expected, unsigned timeout)
{
	simInt master_status = -1;
	simInt status_check_success = 0;
	unsigned trial = 0;
	unsigned time_per_trial = 100000; // microseconds
	unsigned long time_passed = 0;
	std::cout << PLUGIN_MESSAGE_PREFIX << "Waiting for evo-master status " << expected << std::endl;
	while (!(status_check_success == 1 && master_status == expected) && time_passed < (timeout*1000000))
	{
		usleep(time_per_trial);
		status_check_success = simGetIntegerSignal("Evo-Master Status", &master_status);
		trial++;
		time_passed = trial*time_per_trial;
	}
	if (status_check_success == 1 && master_status == expected)
		{
		std::cout << PLUGIN_MESSAGE_PREFIX << "done." << std::endl;
		return true;
		}
	else
		{
		std::cout << PLUGIN_MESSAGE_PREFIX << "Master status update timed out" << std::endl;
		return false;
		}
}

std::vector<std::string> ECGetGenomeFilenamesFromMaster()
{
	std::vector<std::string> filenames;
	simInt n_Genomes = 1;
	simInt path_length;
	simGetIntegerSignal("n_Genomes", &n_Genomes);
	simChar* p_path_to_files;
	const char* c_filepath_signal;
	std::string filepath_signal;
	filepath_signal = "Path_To_Files";
	c_filepath_signal = filepath_signal.c_str();
	p_path_to_files = simGetStringSignal(c_filepath_signal, &path_length);
	std::string str_path_to_files(p_path_to_files);
	std::cout << plugin_message_prefix  << "path to genome files: " << str_path_to_files << std::endl;
	for (unsigned i = 0; i<n_Genomes; i++)
	{
		simChar* p_genome_filename;
		simInt filename_length;
		const char* c_filename_signal;
		std::string filename_signal;
		filename_signal = "Genome_File_Name_";
		// note: the names of the signals for the genome filenames are unique per client only
		filename_signal.append(std::to_string(i));
		c_filename_signal = filename_signal.c_str();
		p_genome_filename = simGetStringSignal(c_filename_signal, &filename_length); // reference parameter can be used as in/output argument
		std::string str_genome_filename(p_genome_filename);
		std::cout << plugin_message_prefix  << "genome file " << i << ": " << str_genome_filename << std::endl;
		std::string file_to_add = str_path_to_files;
		file_to_add.append(str_genome_filename);
		filenames.push_back(file_to_add);
	}
	return filenames;
}

std::vector<std::string> ECCreateGenomeFilenames(std::string base, std::string suffix)
{
	// first, calculate the amount of genomes required for the scene
	std::vector<std::string> filenames;
	unsigned n_genomes_needed = 0;
	for (int botIndex = 0; botIndex < botContainer.size(); botIndex++)
	{
		if (botContainer[botIndex].MemberOfGroup() == -1)
			{
				n_genomes_needed ++;
			}
	}
	for (int cgIndex = 0; cgIndex < cloneGroupContainer.size(); cgIndex++)
	{
		n_genomes_needed ++;
	}
	// now, construct the filenames for the amount of genomes needed
	for (int i_file = 0; i_file < n_genomes_needed; ++i_file)
	{
		std::string new_filename;
		new_filename = base + "_" + std::to_string(clientID) + "_" + std::to_string(i_file) + "." + suffix;
		filenames.push_back(new_filename);
	}
	return filenames;
}

std::vector<NEAT::Genome> ECLoadGenomes(std::vector<std::string>* p_filenames)
{
	//p_filenames could be const >> see const rules (advanced!!)
	std::vector<NEAT::Genome> genomes;
	std::vector<std::string>::iterator iter;
	for (iter = p_filenames->begin(); iter != p_filenames->end(); ++iter)
	{
		std::string filename = *iter;
		const char* c_filename = filename.c_str();
		NEAT::Genome genome(c_filename);
		genomes.push_back(genome);
		std::cout << PLUGIN_MESSAGE_PREFIX << filename << " loaded." << std::endl;
	}
	return genomes;
}

void ECDistributeGenomes(std::vector<NEAT::Genome>* a_genomeContainer)
{
	// first, calculate the amount of genomes required for the scene
	unsigned n_genomes_needed = 0;
	for (int botIndex = 0; botIndex < botContainer.size(); botIndex++)
	{
		if (botContainer[botIndex].MemberOfGroup() == -1) n_genomes_needed ++;
	}
	for (int cgIndex = 0; cgIndex < cloneGroupContainer.size(); cgIndex++)
	{
		n_genomes_needed ++;
	}

	if (a_genomeContainer->size() >= n_genomes_needed)
	{
		// now distribute the genomes to the bots and cloneGroups
		for (int cgIndex = 0; cgIndex < cloneGroupContainer.size(); cgIndex++)
		{
			if (a_genomeContainer->size() > 0)
			{
				NEAT::Genome thisGenome = a_genomeContainer->front();
				a_genomeContainer->erase(a_genomeContainer->begin());
				cloneGroupContainer[cgIndex].SetGenome(thisGenome);
			}
			else
			{
				std::cout << PLUGIN_MESSAGE_PREFIX << "ran out of genomes." << std::endl;
			}
		}
		for (int botIndex = 0; botIndex < botContainer.size(); botIndex++)
		{
			if (botContainer[botIndex].MemberOfGroup() == -1) // will get its own genome if not member of a cloneGroup, otherwise the cloneGroup's genome
			{
				if (a_genomeContainer->size() > 0)
				{
					NEAT::Genome thisGenome = a_genomeContainer->front();
					a_genomeContainer->erase(a_genomeContainer->begin());
					botContainer[botIndex].SetGenome(thisGenome);
				}
				else
				{
					std::cout << PLUGIN_MESSAGE_PREFIX << "ran out of genomes." << std::endl;
				}
			}
			else
			{
				NEAT::Genome thisGenome = cloneGroupContainer[botContainer[botIndex].MemberOfGroup()].GetGenome();
				botContainer[botIndex].SetGenome(thisGenome);
			}
		}
	}
	else
	{
		std::cout << PLUGIN_MESSAGE_PREFIX << "not enough genomes available for the current setup, " << n_genomes_needed << " genomes required" << std::endl;
	}
}


void LUA_TRIGGER_BRAIN_CALLBACK(SLuaCallBack* p)
{
	int found, caller_container_index;
	Bot* current_bot;
	bool commandWasSuccessful = false;
	std::vector<double> NNoutput;
	unsigned short int n_NN_outputs;
	unsigned short int n_NN_inputs;
	int caller_handle = p->objectID;
	std::tie(found, caller_container_index) = ECIdentifyCaller(&caller_handle); //TODO for every sim_step might slow down sim!!!!
	if (found == 1)  //1 means bot
	{
		current_bot = &(botContainer[caller_container_index]);
		n_NN_inputs = current_bot->n_NN_inputs;
		n_NN_outputs = current_bot->n_NN_outputs;
		if (p->inputArgCount == 1)
		{	// Check Type and Size of Arguments from LUA function call
			if ((p->inputArgTypeAndSize[0] == (sim_lua_arg_float|sim_lua_arg_table))  // [0] (==[i*2+0], n_a being the number of arguments) is the type of argument nr. i_a
					&& (p->inputArgTypeAndSize[1] == n_NN_inputs)) 					  // [1] (==[i*2+1]) is the size of the argument table
			{ 	// Arguments ok, now activate brain of Bot and retrieve outputs
				std::vector<double> NNinput;			//	get NN input values from LUA Arguments
				for (int i = 0; i < n_NN_inputs; i++)
				{
					NNinput.push_back(p->inputFloat[i]);
					// DEBUG std::cout << "NN_input " << std::to_string(i) << ": " << NNinput[i] << std::endl;
				}
				NNoutput = botContainer[caller_container_index].BrainResponse(NNinput);
				for (int j = 0; j < n_NN_outputs; j++)
				{
					// DEBUG std::cout << "NN_output" << std::to_string(j) << ": " << NNoutput[j] << std::endl;
				}
				commandWasSuccessful = true;
			}
			else // output an error
				simSetLastError("simextEVO_triggerBrain",
						"Wrong argument type/size.");
		}
		else
			simSetLastError("simextEVO_triggerBrain", "Invalid Number of Arguments.");
		if (!commandWasSuccessful)
			p->outputArgCount=0;
		else
		{ // Command succeeded, we return a float table of size n_NN_outputs
			p->outputArgCount = 1; 																	// 1 return value
			p->outputArgTypeAndSize=(simInt*)simCreateBuffer(p->outputArgCount*2*sizeof(simInt)); 	// x return values takes x*2 simInt for the type and size buffer
			p->outputArgTypeAndSize[0] = (sim_lua_arg_float|sim_lua_arg_table);
			p->outputArgTypeAndSize[1] = n_NN_outputs;

			// Create the float buffer and populate it:
			p->outputFloat=(simFloat*)simCreateBuffer(n_NN_outputs*sizeof(float));
			for (int i=0;i<n_NN_outputs;i++)
				p->outputFloat[i]=float(NNoutput[i]);
		}
	}
	else // object not found in botContainer
	{
		simSetLastError("simextEVO_triggerBrain", "Function not called by a Bot!");
	}
}

void LUA_INIT_EVAL_CALLBACK(SLuaCallBack* p)
{
	int clientIDcheck;
	std::string clientID_signalName = "ClientID_Signal";
	clientIDcheck = simGetIntegerSignal(clientID_signalName.c_str(), &clientID);
	if (clientIDcheck == 1)
	{
		std::cout << PLUGIN_MESSAGE_PREFIX << "starting evaluation..." << std::endl;
		ECAutoRegister(100, 100);
		std::cout << PLUGIN_MESSAGE_PREFIX << "waiting for genomes from evo-master... " << std::endl;
		bool success = WaitForMasterStatus(0, 5);
		if (success == true)
		{
			std::vector<NEAT::Genome> genomes;
			genomeFilenamesContainer = ECCreateGenomeFilenames("genome", "mng");
			genomes = ECLoadGenomes(&genomeFilenamesContainer);
			ECDistributeGenomes(&genomes);
			for (unsigned i=0; i<botContainer.size(); i++)
			{
				botContainer[i].MakeNEATBrain();
				botContainer[i].report();
			}
			std::cout << PLUGIN_MESSAGE_PREFIX << "evaluation launched" << std::endl;
			simSetIntegerSignal("Evo-Client Status", 1); // 1 = evaluating

		}
		else
		{
			std::cout << PLUGIN_MESSAGE_PREFIX << "no genomes loaded" << std::endl;
			simStopSimulation();
		}
	}
	else
	std::cout << plugin_message_prefix << " initialization failed, no client ID retrieved." << std::endl;
}

void LUA_SET_FITNESS_CALLBACK(SLuaCallBack* p)
{
	int caller_handle = p->objectID;
	bool commandWasSuccessful = false;
	// first, identify the caller - search in Bots and CloneGroups. if it's not listed, output an error
	bool found = false;
	int bot_caller_ID;
	int cg_caller_ID;
	int caller_type = -1;
	for (unsigned i=0; i<cloneGroupContainer.size(); i++)
	{
		if (cloneGroupContainer[i].GetHandle() == caller_handle)
			{
			cg_caller_ID = i;
			found = true;
			caller_type = 0;
			break;
			}
	}
	if (found == false)
	{
		for (unsigned i=0; i<botContainer.size(); i++)
		{
			if (botContainer[i].GetHandle() == caller_handle)
			{
				bot_caller_ID = i;
				found = true;
				caller_type = 1;
				break;
			}
		}
	}
	// found it, now see if its a Bot or a CloneGroup and publish the fitness
	if (found == true)
	{
		if (p->inputArgCount == 1)
		{
			if (p->inputArgTypeAndSize[0] == sim_lua_arg_float)
			{
				float fitness;
				fitness = p->inputFloat[0];
				commandWasSuccessful = true;
				if (caller_type == 0)
				{
					cloneGroupContainer[cg_caller_ID].SetCGFitness(fitness);
					cloneGroupContainer[cg_caller_ID].PublishFitnessScore();
				}
				if (caller_type == 1)
				{
					if (botContainer[bot_caller_ID].MemberOfGroup() == -1)
					{
						botContainer[bot_caller_ID].SetBotFitness(fitness);
						botContainer[bot_caller_ID].PublishFitnessScore();
						//DEBUG std::cout << plugin_message_prefix << botContainer[bot_caller_ID].GetName() << ": fitness is " << botContainer[bot_caller_ID].GetGenome().GetFitness() << std::endl;
					}
					else
					{
						std::cout << PLUGIN_MESSAGE_PREFIX << botContainer[bot_caller_ID].GetName()
								   << " is part of a cloneGroup and cannot set its own fitness" << std::endl;
					}
				}
			}
			else
				simSetLastError("simextEVO_setFitness", "Wrong argument type/size.");
		}
		else
			simSetLastError("simextEVO_setFitness", "Invalid Number of Arguments.");
	}
	else
		simSetLastError("simextEVO_setFitness", "Function called by an unregistered object. Does it conform to the naming conventions for evaluators?");
}

void LUA_END_EVAL_CALLBACK(SLuaCallBack* p)
{
	simSetIntegerSignal("Evo-Client Status", 2);	// 2 =  evaluation finished
	std::cout << PLUGIN_MESSAGE_PREFIX << "evaluation finished" << std::endl;
	simPauseSimulation();
}

void LUA_BUILD_BRAIN_CALLBACK(SLuaCallBack* p)
{
    int caller_handle = p->objectID;
    bool commandWasSuccessful = false;
    bool found = false;
    std::string thisBotName;
    thisBotName = simGetObjectName(caller_handle);
    Bot newBot(thisBotName);
    botContainer.push_back(newBot);

    std::cout << PLUGIN_MESSAGE_PREFIX << "here1" << std::endl;
    if (p->inputArgCount == 1)
    {	// Check Type and Size of Arguments from LUA function call
        if (p->inputArgTypeAndSize[0] == sim_lua_arg_string)
        {
            std::cout << PLUGIN_MESSAGE_PREFIX << "here2" << std::endl;
            std:string filename;
            filename = p->inputChar;
            std::cout << PLUGIN_MESSAGE_PREFIX << "filename: " << filename << std::endl;
            newBot.MakeNEATBrainFromFile(filename);
            commandWasSuccessful = true;
            std::cout << PLUGIN_MESSAGE_PREFIX << "here3" << std::endl;
        }
        else // output an error
            simSetLastError("simextEVO_buildBrain",
                            "Wrong argument type/size.");
    }
    else
        simSetLastError("simextEVO_buildBrain", "Invalid Number of Arguments.");
    if (!commandWasSuccessful)
        p->outputArgCount=0;
    else
    { // Command succeeded, we return a float table of size n_NN_outputs
        std::cout << PLUGIN_MESSAGE_PREFIX << "here7" << std::endl;
        p->outputArgCount=1;
        std::cout << PLUGIN_MESSAGE_PREFIX << "here8" << std::endl;
        // TODO
    }

}


/***********************Plugin Entry Points :**************************************/

void ECPluginLoad()
{

	simSetIntegerSignal("Evo-Client Status", -1); 	// -1 = not ready/error
	sim_start_counter = 0;
	/*
	 * http://www.coppeliarobotics.com/helpFiles/en/apiFunctions.htm#simAuxiliaryConsoleOpen
	const simChar* title = "testtest";
	simInt maxLines = 100;
	simInt mode = 0;
	const simInt position[2]  = {100,100};
	const simInt size[2] = {500,300};
	const simFloat textColor[3] = {0,0,0};
	const simFloat backgrColor[3] = {1,1,1};
	simAuxiliaryConsoleOpen(title,maxLines,mode,position,size,textColor,backgrColor);
	 */
}

void ECPluginSimAboutToStart()
{
	//DEBUG:
	simSetIntegerSignal("counter", sim_start_counter);
}

void ECPluginSceneLoaded()
{
	simSetIntegerSignal("Evo-Client Status", 0);	// 0 = sim stopped
}

void ECPluginSimStep()
{
}

void ECPluginSimFinished()
{
	simClearFloatSignal(NULL);
    simClearIntegerSignal(NULL);
	std::cout << PLUGIN_MESSAGE_PREFIX << "stopped" << std::endl;
	sim_start_counter++;
	simSetIntegerSignal("Evo-Client Status", 0); 	// 0 = sim stopped
}


/* Snippets
 *
 *
// DEPRECATED:
void ECGenomesToBots(std::vector<NEAT::Genome> genomes)
// TODO: Update for CloneGroups
{
	int bots_per_genome = botContainer.size() / genomes.size();
	int last_j = 0;
	for (int i = 0; i < genomes.size(); i++)
	{
		for (int j = i * bots_per_genome; j < (i+1) * bots_per_genome; j++)
		{
			NEAT::Genome genome = genomes.at(i);
			botContainer[j].SetGenome(genome);
			std::cout << plugin_message_prefix  << botContainer[j].GetName() << " received genome " << genome.GetID() << std::endl ;
			last_j = j;
		}
	}
	for (int k = last_j+1; k < botContainer.size(); k++)
	{
		NEAT::Genome genome = genomes.back();
		botContainer[k].SetGenome(genome);
		std::cout << plugin_message_prefix  << botContainer[k].GetName() << " received genome " << genome.GetID() << std::endl;
	}
	genomes.clear();
}

// DEPRECATED:
void ECPublishFitnessAll()
{
	for (int cgIndex = 0; cgIndex < cloneGroupContainer.size(); cgIndex++)
	{
		cloneGroupContainer[cgIndex].PublishFitnessScore();
	}
	for (int botIndex = 0; botIndex < botContainer.size(); botIndex++)
	{
		if (botContainer[botIndex].MemberOfGroup() == -1)
		{
			botContainer[botIndex].PublishFitnessScore();
		}
	}
}
*/
