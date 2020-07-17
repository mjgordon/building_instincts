"""
Created on Mar 10, 2015
@author: raimund
raimund.krenmueller@iaac.net

TODO 4/15/2020:
pause evolution + safe population
automate unique filename for best_ever

"""

from __future__ import print_function
import matplotlib
matplotlib.use('TkAgg', force=True)
import MultiNEAT as MN
import os
import vrep
import random
from time import time, sleep

cwd = os.getcwd()

# Visualisation
mpl_monitor = True
exp_title = 'Brick Stacking'
eval_scene = cwd + '/eval_scenes/balancing_2020.ttt'
#eval_scene = cwd + '/eval_scenes/WS_BoxPushing_random.ttt'
exp_subtitle = 'SCENE: ' + eval_scene
pdf_filename = 'brick_stacking.pdf'  # TODO: automate unique filename creation

# Saving and Loading
genome_suffix = '.mng'              # default = '.mng' (MultiNeatGenome)
start_from_seed = False             # if true, initialise 1st generation using an existing genome, ...
seed_file_name = 'best_brains/best_brain_2020'       # ... this one (location: evo_master folder)
safe_bestever = True                # is true, safe best of the evaluation, ...
chosen_one_name = cwd + '/best_brains/best_brain_2020'     # ... using this filename + genome_suffix
#chosen_one_name = cwd + '/best_brains/best_brain_WS_BoxPushing'     # ... using this filename + genome_suffix
path_to_gene_pool = cwd + '/gene_pool/'  # -> where all genome files reside on the evo_master side

# Debug
verbose = True

# EVO NET CONFIG
client_connection_timeout = 1000
client_comm_cycle_time = 10  # default: 10
#evo_client_map = {'127.0.0.1': [19997]}
evo_client_map = {'127.0.0.1': [19997, 19996, 19995, 19994]}
#evo_client_map = {'127.0.0.1': [19997, 19996, 19995, 19994, 19993, 19992, 19991, 19990, 19989, 19988]}
genomes_per_client_each = []
genomes_per_client_all = 20  # -1 to use list 'genomes_per_client_each', otherwise this amount is used for every client

# NEURO CONFIG

nr_NN_ins = 6  # always add one extra input, used as bias unit
nr_NN_hidden = 0  # if > 0, start_minimal must be false!!
nr_NN_outs = 4
start_minimal = False

#nr_NN_ins = 13  # always add one extra input, used as bias unit
#nr_NN_hidden = 0  # if > 0, start_minimal must be false!!
#nr_NN_outs = 2
#start_minimal = False

# MULTINEAT CONFIG
para_file = cwd + '/params.mnp'
params = MN.Parameters()  # params.PopulationSize is set by init_pop
random_seed = 0

# MY EVO CONFIG
n_generations = 100000
timeout_one_gen = 90  # seconds

# VREP COMM MODES
mode1 = vrep.simx_opmode_oneshot
mode2 = vrep.simx_opmode_oneshot_wait
mode3 = vrep.simx_opmode_buffer
mode4 = vrep.simx_opmode_streaming + 50
mode5 = vrep.simx_opmode_discontinue
mode6 = vrep.simx_opmode_blocking


class Evo_Client(object):
    """
    Represents a single evo_client instance with plugin loaded
    """
    def __init__(self, ip, port, n_genomes):
        """
        Constructor
        """
        self.health_initial = 5
        self.health = self.health_initial
        self.ip = ip
        self.port = port
        self.amount_of_genomes = n_genomes
        self.genome_filenames = []
        self.genomes = []
        self.status = -1
        self.__old_status = -2
        self.is_online = False
        self.was_online = False
        self.clientID = vrep.simxStart(self.ip, self.port, True, False, client_connection_timeout,
                                       client_comm_cycle_time)
        # subscribe to streaming
        vrep.simxGetIntegerSignal(self.clientID, 'Evo-Client Status', mode4)  

    def update_status(self):
        """
        check the status of the simulator
        """
        self.status_has_changed = False
        self.is_online = False
        if vrep.simxGetConnectionId(self.clientID) != -1 and self.clientID != -1:
            success, self.status = vrep.simxGetIntegerSignal(self.clientID, 'Evo-Client Status', mode4)            
            self.is_online = True  
            if self.status != self.__old_status: self.status_has_changed = True         
            self.__old_status = self.status
            # -1 = not ready/error, 0 = ready, 1 = active, 2 = done                         
        return self.status 
               
    def save_genomes_to_files(self):
        """
        save the genomes associated with this client
        """
        if not self.genome_filenames:
            for i in range(len(self.genomes)):
                    this_genome_filename = 'genome_' + str(self.clientID) + '_' + str(i) + genome_suffix            
                    self.genome_filenames.append(this_genome_filename)  
   
        for this_genome, this_genome_filename in zip(self.genomes, self.genome_filenames):
            this_genome.Save(path_to_gene_pool + this_genome_filename)
               
    def transfer_genomes(self, timeout):
        """
        transfer the genome files to the evo-client
        """
        ret, ping_time = vrep.simxGetPingTime(self.clientID)   
        checksum = 0
        vrep.simxClearIntegerSignal(self.clientID, "ClientID_Signal", mode1)
        vrep.simxSetIntegerSignal(self.clientID, "ClientID_Signal", self.clientID, mode1)
        for i, filename in enumerate(self.genome_filenames):
            file_to_transfer = path_to_gene_pool + filename
            ret = vrep.simxTransferFile(self.clientID, file_to_transfer, filename, timeout, mode1) #default: mode2
            if ret == 0: checksum += 1                     
        return checksum
           
    def end(self):
        """
        close connection
        """
        vrep.simxFinish(self.clientID)   
                 
    def send_master_status(self, master_status):
        """
        announce a new evo master status
        """
        vrep.simxSetIntegerSignal(self.clientID, 'Evo-Master Status', master_status, mode1)
        
    def launch(self):
        """
        trigger simulations start
        """
        ret = vrep.simxStartSimulation(self.clientID, mode1)
        return ret
    
    def reset(self):
        """
        stop the simulation (will reset the scene in vrep)
        clear signals and erase the client's local genome files
        """
        ret = vrep.simxStopSimulation(self.clientID, mode1)        
        for filename in self.genome_filenames:
            vrep.simxEraseFile(self.clientID, filename, mode1)  
        vrep.simxClearIntegerSignal(self.clientID, '', mode1)
        vrep.simxClearFloatSignal(self.clientID, '', mode1)   
        vrep.simxClearStringSignal(self.clientID, '', mode1)

    def grab_new_genomes(self, gene_pool):
        """
        clears old genomes assigned to this client and assigns new ones to evaluate
        """
        self.genomes = []
        for i in range(self.amount_of_genomes):
            this_genome = gene_pool.pop(0)
            self.genomes.append(this_genome)
            
    def load_scene(self, scene_path_and_filename):
        """
        remotely load the scene in client from file located at evo_master
        """
        ret = vrep.simxLoadScene(self.clientID, scene_path_and_filename, 1, mode2)
        return ret
    
    def init_fitness_streaming(self):
        """
        subscribe to the fitness streams associated with this client
        """
        for genome in self.genomes:
            genome_ID = genome.GetID()
            sig_name = 'FitnessScore_' + str(genome_ID)       
            vrep.simxGetFloatSignal(self.clientID, sig_name, mode4)
        
    def update_fitness_scores(self, print_report):
        """
        fetch fitness values from vrep and save to python genomes
        """
        for genome in self.genomes:
            genome_ID = genome.GetID()
            sig_name = 'FitnessScore_' + str(genome_ID)       
            ret, fitness = vrep.simxGetFloatSignal(self.clientID, sig_name, mode4)
            if print_report:
                print("client", self.clientID, ": genome", genome_ID, "has", sig_name, ": ", fitness, "success: ", ret)
            if ret == 0:
                genome.SetEvaluated()
                genome.SetFitness(fitness)

    def stop_fitness_streaming(self):
        """
        unsubscribe from streaming fitness signals at the end of every generation:
        otherwise streaming will continue, subscriptions pile up and block python
        """
        for genome in self.genomes:
            genome_ID = genome.GetID()
            sig_name = 'FitnessScore_' + str(genome_ID)
            vrep.simxGetFloatSignal(self.clientID, sig_name, mode5)
            
    def recover(self):
        """
        attempt to restore connection to a lost client
        """
        if self.clientID != -1: 
            # this check is necessary,
            # otherwise a client that was not online when created (ID == -1) would lead to simxFinish(-1),
            # which kills ALL connections
            vrep.simxFinish(self.clientID)
        new_clientID = vrep.simxStart(self.ip,self.port, False, True, client_connection_timeout, client_comm_cycle_time)
        # vrep.simxStart(connectionAddress, connectionPort, waitUntilConnected, doNotReconnectOnceDisconnected,
        # timeOutInMs, commThreadCycleInMs)
        if vrep.simxGetConnectionId(self.clientID) != -1 and new_clientID != -1:
            self.clientID = new_clientID
            self.health = self.health_initial
            self.is_online = True
            success = True
        else:
            success = False
        return success


def init_evo_net(evo_net_mapping, genome_distribution, n_genomes_default):
    """
    Instantiate Client Objects and connect to Evo_Clients
    """
    evo_clients = [] 
    client_index = 0 
    n_clients_in_map = 0
    for ip, ports in evo_net_mapping.items(): 
        for port in ports:
            n_clients_in_map += 1   

    for ip, ports in evo_net_mapping.items():  
        for port in ports:
            if n_genomes_default != -1:
                n_genomes = n_genomes_default                                  
            else:
                # TODO: what if index out of range?
                n_genomes = genome_distribution[client_index]
            new_client = Evo_Client(ip, port, n_genomes) 
            new_client.update_status()
            if new_client.is_online:                
                if verbose:
                    print("found client", new_client.clientID, "at", ip, ":", port)
            else:
                if verbose:
                    print("no client found at ", ip, ":", port)
            evo_clients.append(new_client)  # append in any case, might come online later
            client_index += 1
    return evo_clients


def init_pop(evo_clients):
    pop_size_required = 0
    for i, client in enumerate(evo_clients):  # determine total number of genomes needed
        if genomes_per_client_all != -1:    # -1 means use list 'genomes_per_client_each' 
            pop_size_required += genomes_per_client_all
        else:
            try:
                pop_size_required += genomes_per_client_each[i]
            except:
                pop_size_required += genomes_per_client_all
    MN.Parameters.Load(params, para_file)
    params.PopulationSize = pop_size_required
    genome = MN.Genome(0, nr_NN_ins, nr_NN_hidden, nr_NN_outs, start_minimal,
                       MN.ActivationFunction.UNSIGNED_SIGMOID,
                       MN.ActivationFunction.UNSIGNED_SIGMOID, 1, params, 0)
    pop = MN.Population(genome, params, True, 1.0, random_seed)  # randomized for first gen
    return pop, pop_size_required


def pop_from_seed(evo_clients, a_seed_genome):
    pop_size_required = 0
    for i, client  in enumerate(evo_clients):
        if genomes_per_client_all != -1:    # -1 means use list 'genomes_per_client_each'
            pop_size_required += genomes_per_client_all
        else:
            try:
                pop_size_required += genomes_per_client_each[i]
            except:
                pop_size_required += genomes_per_client_all
    params.PopulationSize = pop_size_required;
    pop = MN.Population(a_seed_genome, params, False, 0.1, 1)
    return pop, pop_size_required


def prepare_eval(client, eval_scene, lock):       
    if client.is_online:
        client.reset()
        sleep(0.3)
        ret = client.load_scene(eval_scene)
        if verbose:
            lock.acquire()
            if ret == 0: print("client", client.clientID, "scene loaded.")
            elif ret == 2:
                print("client", client.clientID, "load scene: command timed out")
            else:
                print("client", client.clientID, "load scene: command returned: ", ret)
            lock.release()


def init_eval(client, gene_pool, eval_scene, lock):
    client.update_status()
    if not client.is_online:                  
        if verbose: print("client at", client.ip, ':', client.port, "is offline.")
        oldID = client.clientID
        if client.health > 0:
            success = client.recover()            
            if success:
                if verbose: print("client at", client.ip, ':', client.port, "was recovered as client", client.clientID)
                client.load_scene(eval_scene)
            else:
                if verbose: print("client at", client.ip, ':', client.port, "lost, recovery failed")
                client.health -= 1
        elif client.health == 0: 
            if verbose: print("client at", client.ip, ':', client.port, "is unresponsive and had to be dropped")
            client.health -= 1
        else:
            client.health -= 1
            pass  # maybe try to resurrect client after certain n of gens
                                                                                  
    if client.is_online:
        client.was_online = True 
        lock.acquire()           
        client.grab_new_genomes(gene_pool) 
        lock.release()       
        client.save_genomes_to_files()
        then = time()
        checksum = client.transfer_genomes(timeout = 500) # ms
        
        lock.acquire()
        if checksum == len(client.genomes): print("client", client.clientID, "all genomes transferred in",
                                                  time() - then, "seconds")
        else:
            print("client", client.clientID, len(client.genomes) - checksum, "genomes could not be transferred")
        lock.release()
        
        client.send_master_status(0) 
        client.init_fitness_streaming()  
        ret = client.launch()        
        if verbose: 
            lock.acquire()
            if ret == 0 or ret == 1: print("client", client.clientID, "evaluation launched")
            elif ret == 2:
                print("client", client.clientID, "launch evaluation: command timed out")
            else:
                print("client", client.clientID, "launch evaluation: command returned: ", ret)
            lock.release()


def monitor_eval(client, lock):
    then = time()                        
    time_passed = 0
    step_counter = 0                    
    eval_done = False   
    while not eval_done:                        
        now = time()    
        time_passed = now - then
        if time_passed > timeout_one_gen: 
            lock.acquire()
            print("client", client.clientID, "evaluation timed out")
            lock.release()
            vrep.simxPauseSimulation(client.clientID, mode1)                    
            if client.status == 1: 
                client.update_fitness_scores(print_report = False)                                                               
            eval_done = True
        else:                   
            if step_counter % 3 == 0:
                eval_done = True 
                client.update_status()                                            
                if client.is_online:                                                             
                    if client.status != 2 or time_passed < 1.0: 
                        client.update_fitness_scores(print_report = False)
                        eval_done = False
                    else:                             
                        client.update_fitness_scores(print_report = False) # fitness_report_please[i])
                else:
                    if client.was_online:
                        lock.acquire()
                        print("client", client.clientID, "went offline during evaluation.")
                        lock.release()
                        client.was_online = False   
                    pass #client.ignore
        sleep(0.3)     
    client.stop_fitness_streaming() 
    if client.is_online:            
        client.reset()
        client.send_master_status(-1)
        if verbose:
            lock.acquire()
            print("client", client.clientID, "evaluation finished")
            lock.release()
        
    
# ______________________UTILITIES_________________________

def kill_clients():
        vrep.simxFinish(-1)


def set_random_fitness(pop):
    # debug function: assign a random fitness value to all individuals in a population
    genome_list = MN.GetGenomeList(pop)
    for genome in genome_list:
        fitness = random.random()
        genome.SetFitness(fitness)


'''

# OLD STUFF    
    
def genomes_to_clients(evo_clients, pop):
    genome_list = MN.GetGenomeList(pop)         
    
    for j, client  in enumerate(evo_clients):
        if genomes_per_client_each[j] == -1:    # -1 means use default value 
            n_genomes_this_client = genomes_per_client_all
        else: 
            n_genomes_this_client = genomes_per_client_each[j]
            
        if client.is_online:
            client.genomes = []
            if verbose: print "genomes to be evaluated by client ", client.clientID, ":"
            for k in range(0, n_genomes_this_client):
                this_genome = genome_list.pop(0)                
                client.add_genome(this_genome)
                if verbose: print "    genome", this_genome.GetID()                                      
        else:
            if verbose: print "client ", client.clientID, "is offline"

____________

if __name__ == '__main__':
    m_fitness = MN.Genome.GetFitness(member)
    print m_fitness
    MN.Genome.SetFitness(member, 1.3)
    m_fitness = MN.Genome.GetFitness(member)
    print m_fitness
    MN.Genome.Save(member, 'genome_save_test')
    
      
______________

pop = vrMN.init_pop()
vrMN.set_random_fitness(pop)
genome_list = MN.GetGenomeList(pop)
generation_counter = 0
pop_name = "population_gen" + str(generation_counter)
pop.Save(pop_name)
genome_index = 0
for genome in genome_list:
    genome_name = "gen" + str(generation_counter) + "_id" + str(genome_index) + ".mn"  # gen0_id0.mn
    genome_index += 1
    vrMN.MN.Genome.Save(genome, genome_name)
    fitness = vrMN.MN.Genome.GetFitness(genome)
    print fitness
___________________

"""Evo_Client Class Ex-Members

    def OLD_publish_filenames(self):
        """
        DEPRECATED
        tell vrep client how many and which genome files to load
        """
        raw_ubytes_path = (ctypes.c_ubyte * len(path_to_gene_pool)).from_buffer_copy(path_to_gene_pool)
        vrep.simxSetStringSignal(self.clientID,'Path_To_Files', raw_ubytes_path, mode1)
        vrep.simxSetIntegerSignal(self.clientID, 'n_Genomes', len(self.genomes), mode1)
        if verbose: print "publishing filenames for evo-client", self.clientID, ",", len(self.genomes), "files"
        for i, (genome, filename) in enumerate(zip(self.genomes, self.genome_filenames)):
            # now convert string to c_ubyte:  (see http://www.forum.coppeliarobotics.com/viewtopic.php?f=5&t=3237) 
            raw_ubytes_filename = (ctypes.c_ubyte * len(filename)).from_buffer_copy(filename)
            vrep.simxSetStringSignal(self.clientID, ('Genome_File_Name_' + str(i)), raw_ubytes_filename, mode1)
            
    def EXPERIMENTAL_get_fitness_scores(self, print_report):
        """
        fetch fitness values from vrep and save to python genomes 
        """
        for genome, filename in zip(self.genomes, self.genome_filenames):
            sig_name = filename + "_FitnessScore"
            ret, fitness = vrep.simxGetFloatSignal(self.clientID, sig_name, mode4)
            if print_report: print "client", self.clientID, ": genome", genome.GetID(), "in file", filename, "has", sig_name, ": ", fitness, "success: ", ret
            if ret == 0:
                genome.SetEvaluated()
                genome.SetFitness(fitness)
                
    def OLD_add_genome(self, a_genome):
        """
        DEPRECATED
        adds a genome to be evaluated by this client, and subscribes to its fitness message
        """
        self.genomes.append(a_genome)      
        genome_ID = a_genome.GetID()
        vrep.simxGetFloatSignal(self.clientID, 'FitnessScore_' + str(genome_ID), mode4)

___________________

# SNIPPETS

class _Getch:
    """Gets a single character from standard input.  Does not echo to the
    screen.
    from http://stackoverflow.com/questions/510357/python-read-a-single-character-from-the-user/21659588#21659588"""
    def __init__(self):
        try:
            self.impl = _GetchWindows()
        except ImportError:
            self.impl = _GetchUnix()

    def __call__(self): return self.impl()


class _GetchUnix:
    def __init__(self):
        import tty, sys

    def __call__(self):
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch


class _GetchWindows:
    def __init__(self):
        import msvcrt

    def __call__(self):
        import msvcrt
        return msvcrt.getch()


getch = _Getch()


simx_return_ok (0)
The function executed fine

simx_return_novalue_flag (1 (i.e. bit 0))
There is no command reply in the input buffer. This should not always be considered as an error, depending on the selected operation mode

simx_return_timeout_flag (2 (i.e. bit 1))
The function timed out (probably the network is down or too slow)

simx_return_illegal_opmode_flag (4 (i.e. bit 2))
The specified operation mode is not supported for the given function

simx_return_remote_error_flag (8 (i.e. bit 3))
The function caused an error on the server side (e.g. an invalid handle was specified)

simx_return_split_progress_flag (16 (i.e. bit 4))
The communication thread is still processing previous split command of the same type

simx_return_local_error_flag (32 (i.e. bit 5))
The function caused an error on the client side

simx_return_initialize_error_flag (64 (i.e. bit 6))
simxStart was not yet called

'''  
