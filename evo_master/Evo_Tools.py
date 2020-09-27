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
import sim
import random
from time import time, sleep

cwd = os.getcwd()

# Saving and Loading
genome_suffix = '.mng'  # default = '.mng' (MultiNeatGenome)

# Debug
verbose = True

# EVO NET CONFIG
client_connection_timeout = 1000
client_comm_cycle_time = 10  # default: 10
evo_client_map = {}


# MULTINEAT CONFIG
para_file = cwd + '/params.mnp'
params = MN.Parameters()  # params.PopulationSize is set by init_pop
random_seed = 0

# MY EVO CONFIG
n_generations = 100000
timeout_one_gen = 300  # seconds

# VREP COMM MODES
mode1 = sim.simx_opmode_oneshot
mode2 = sim.simx_opmode_oneshot_wait
mode3 = sim.simx_opmode_buffer
mode4 = sim.simx_opmode_streaming + 50
mode5 = sim.simx_opmode_discontinue
mode6 = sim.simx_opmode_blocking


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
        self.clientID = sim.simxStart(self.ip, self.port, True, False, client_connection_timeout,
                                       client_comm_cycle_time)
        # subscribe to streaming
        sim.simxGetIntegerSignal(self.clientID, 'Evo-Client Status', mode4)

    def update_status(self):
        """
        check the status of the simulator
        """
        self.status_has_changed = False
        self.is_online = False
        if sim.simxGetConnectionId(self.clientID) != -1 and self.clientID != -1:
            success, self.status = sim.simxGetIntegerSignal(self.clientID, 'Evo-Client Status', mode4)
            self.is_online = True
            if self.status != self.__old_status: self.status_has_changed = True
            self.__old_status = self.status
            # -1 = not ready/error, 0 = ready, 1 = active, 2 = done
        return self.status

    def save_genomes_to_files(self, project):
        """
        save the genomes associated with this client
        """
        if not self.genome_filenames:
            for i in range(len(self.genomes)):
                    this_genome_filename = 'genome_' + str(self.clientID) + '_' + str(i) + genome_suffix
                    self.genome_filenames.append(this_genome_filename)

        for this_genome, this_genome_filename in zip(self.genomes, self.genome_filenames):
            this_genome.Save(project.path_to_gene_pool + this_genome_filename)

    def transfer_genomes(self, timeout, project):
        """
        transfer the genome files to the evo-client
        """
        ret, ping_time = sim.simxGetPingTime(self.clientID)
        checksum = 0
        sim.simxClearIntegerSignal(self.clientID, "ClientID_Signal", mode1)
        sim.simxSetIntegerSignal(self.clientID, "ClientID_Signal", self.clientID, mode1)
        for i, filename in enumerate(self.genome_filenames):
            file_to_transfer = project.path_to_gene_pool + filename
            ret = sim.simxTransferFile(self.clientID, file_to_transfer, filename, timeout, mode1) #default: mode2
            if ret == 0: checksum += 1
        return checksum

    def end(self):
        """
        close connection
        """
        sim.simxFinish(self.clientID)

    def send_master_status(self, master_status):
        """
        announce a new evo master status
        """
        sim.simxSetIntegerSignal(self.clientID, 'Evo-Master Status', master_status, mode1)

    def launch(self):
        """
        trigger simulations start
        """
        ret = sim.simxStartSimulation(self.clientID, mode1)
        return ret

    def reset(self):
        """
        stop the simulation (will reset the scene in vrep)
        clear signals and erase the client's local genome files
        """
        ret = sim.simxStopSimulation(self.clientID, mode1)
        for filename in self.genome_filenames:
            sim.simxEraseFile(self.clientID, filename, mode1)
        sim.simxClearIntegerSignal(self.clientID, '', mode1)
        sim.simxClearFloatSignal(self.clientID, '', mode1)
        sim.simxClearStringSignal(self.clientID, '', mode1)

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
        ret = sim.simxLoadScene(self.clientID, scene_path_and_filename, 1, mode2)
        return ret

    def init_fitness_streaming(self):
        """
        subscribe to the fitness streams associated with this client
        """
        for genome in self.genomes:
            genome_ID = genome.GetID()
            sig_name = 'FitnessScore_' + str(genome_ID)
            sim.simxGetFloatSignal(self.clientID, sig_name, mode4)

    def update_fitness_scores(self, print_report):
        """
        fetch fitness values from vrep and save to python genomes
        """
        for genome in self.genomes:
            genome_ID = genome.GetID()
            sig_name = 'FitnessScore_' + str(genome_ID)
            ret, fitness = sim.simxGetFloatSignal(self.clientID, sig_name, mode4)
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
            sim.simxGetFloatSignal(self.clientID, sig_name, mode5)

    def recover(self):
        """
        attempt to restore connection to a lost client
        """
        if self.clientID != -1:
            # this check is necessary,
            # otherwise a client that was not online when created (ID == -1) would lead to simxFinish(-1),
            # which kills ALL connections
            sim.simxFinish(self.clientID)
        new_clientID = sim.simxStart(self.ip,self.port, False, True, client_connection_timeout, client_comm_cycle_time)
        # sim.simxStart(connectionAddress, connectionPort, waitUntilConnected, doNotReconnectOnceDisconnected,
        # timeOutInMs, commThreadCycleInMs)
        if sim.simxGetConnectionId(self.clientID) != -1 and new_clientID != -1:
            self.clientID = new_clientID
            self.health = self.health_initial
            self.is_online = True
            success = True
        else:
            success = False
        return success

def create_gene_pool_folder(current_project):
    path_to_gene_pool = current_project.path_to_gene_pool  # -> where all genome files reside on the evo_master side
    if not os.path.exists(path_to_gene_pool):
        os.mkdir(path_to_gene_pool)
        print("Project Gene Pool Directory", path_to_gene_pool, "created ")
    else:
        print("Project Gene Pool Directory", path_to_gene_pool, "already exists")


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


def init_pop(evo_clients, current_project):
    pop_size_required = 0
    for i, client in enumerate(evo_clients):  # determine total number of genomes needed
        pop_size_required += current_project.genomes_per_client
    MN.Parameters.Load(params, para_file)
    params.PopulationSize = pop_size_required
    genome = MN.Genome(0,
                       current_project.nn_in, current_project.nn_hidden, current_project.nn_outs, current_project.nn_start_minimal,
                       MN.ActivationFunction.UNSIGNED_SIGMOID,
                       MN.ActivationFunction.UNSIGNED_SIGMOID, 1, params, 0)
    pop = MN.Population(genome, params, True, 1.0, random_seed)  # randomized for first gen
    return pop, pop_size_required


def pop_from_seed(evo_clients, a_seed_genome, current_project):
    pop_size_required = 0
    for i, client  in enumerate(evo_clients):
            pop_size_required += current_project.genomes_per_client
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


def init_eval(client, gene_pool, eval_scene, lock, current_project):
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
        client.save_genomes_to_files(current_project)
        then = time()
        checksum = client.transfer_genomes(timeout = 500, project = current_project) # ms

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
            sim.simxPauseSimulation(client.clientID, mode1)
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
        sim.simxFinish(-1)


def set_random_fitness(pop):
    # debug function: assign a random fitness value to all individuals in a population
    genome_list = MN.GetGenomeList(pop)
    for genome in genome_list:
        fitness = random.random()
        genome.SetFitness(fitness)


