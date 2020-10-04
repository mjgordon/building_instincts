"""
Created on Mar 10, 2015
@author: raimund
raimund.krenmueller@iaac.net
"""

from __future__ import print_function
import threading as thrd
import Evo_Tools as ET
import Evo_Visualize as visualize
import os
import time
from Evo_Project import EvoProject
from MultiNEAT import GetGenomeList, Genome, NeuralNetwork,Population


# Name of project folder to load
project_name = 'balancing'

# This is a bit hacky for the moment, need to make these persistent after moving generation into a function
# May be a better way
bestever = None
best_ever_gen = None
best_ever_fitn = None


def main():
    cwd = os.getcwd()
    print(cwd)

    # Project configuration currently being trained
    current_project = EvoProject(project_name)

    ET.kill_clients()
    n_clients_online = 0
    print("initializing evo-network...")
    ET.evo_client_map[current_project.client_ip] = list(range(19997, 19997 - current_project.client_count, -1))

    evo_clients = ET.init_evo_net(ET.evo_client_map, current_project.genomes_per_client, current_project.genomes_per_client)
    for client in evo_clients:
        client.reset()
        client.update_status()
        if client.is_online:
            n_clients_online += 1

    if n_clients_online > 0:
        print(len(evo_clients), "client(s) created, ", n_clients_online, "online")
        if current_project.start_from_file:
            pop, pop_size_init = ET.init_pop_from_file(current_project)
        # Load best genomes from seed file
        elif current_project.start_from_seed:
            seed_genome = Genome(current_project.seed_load_name + ET.genome_suffix)
            print("starting from seed genome in file", current_project.seed_load_name + ET.genome_suffix, ", genome ID:",
                  seed_genome.GetID())
            pop, pop_size_init = ET.init_pop_from_seed(len(evo_clients) * current_project.genomes_per_client, seed_genome, current_project)
            seed_genome.Save('seed_from' + ET.genome_suffix)
        # Create new randomized genomes
        else:
            pop, pop_size_init = ET.init_pop_new(len(evo_clients) * current_project.genomes_per_client, current_project)

        print("The population comprises", pop_size_init, "genomes")
        prepare_eval_threads = []
        lock = thrd.Lock()
        for client in evo_clients:
            new_thrd = thrd.Thread(target=ET.prepare_eval, args=(client, current_project.eval_scene, lock))
            prepare_eval_threads.append(new_thrd)
            new_thrd.start()
        for thread in prepare_eval_threads:
            thread.join()

        #    prepare plotting stuff:    
        if current_project.start_from_seed:
            show_seed = current_project.seed_load_name
        else:
            show_seed = False
        if current_project.save_best_genome:
            show_bestever = current_project.seed_save_name
        else:
            show_bestever = False
        if current_project.mpl_monitor:
            fig = visualize.init_plot()

        viz = visualize.Visualization(fig)

        # Run main generation loop
        for generation_id in range(ET.n_generations):
            evaluate_generation(generation_id, current_project, pop, evo_clients, viz, n_clients_online)

        # Close client connections
        for client in evo_clients:
            if client.is_online:
                client.end()

    else:
        print("no clients online")

    print("program ended")


def evaluate_generation(generation_id, current_project, pop, evo_clients, viz,n_clients_online):
    """ Evaluate a single generation"""
    global bestever, best_ever_gen, best_ever_fitn
    if current_project.mpl_monitor:
        visualize.set_timer_starttime('current')
    print("")
    print("___________________ next generation:", generation_id, "___________________")

    # create and launch initialization threads:
    print('launching evaluations...')
    gene_pool = GetGenomeList(pop)
    init_eval_threads = []
    lock = thrd.RLock()
    for client in evo_clients:
        new_thrd = thrd.Thread(target=ET.init_eval,
                               args=(client, gene_pool, current_project.eval_scene, lock, current_project))
        init_eval_threads.append(new_thrd)
        new_thrd.start()
    for thread in init_eval_threads:
        try:
            thread.join()
        except:
            pass

    # create and launch monitoring threads
    print('evaluating...')
    monitor_eval_threads = []
    lock = thrd.RLock()
    for client in evo_clients:
        new_thrd = thrd.Thread(target=ET.monitor_eval, args=(client, lock))
        monitor_eval_threads.append(new_thrd)
        new_thrd.start()
    for thread in monitor_eval_threads:
        try:
            thread.join()
        except:
            pass

    # all evaluations done, now print some stats & save the best genome
    print('evaluations done.')
    genome_list = GetGenomeList(pop)
    fitn_list = []
    for genome in genome_list:
        fitn_list.append(genome.GetFitness())
    #print(fitn_list)
    av_fitn = sum(fitn_list) / float(len(fitn_list))
    best_now = pop.GetBestGenome()  # best of the current generation
    best_now_fitn = best_now.GetFitness()
    best_fitn_yet = pop.GetBestFitnessEver()
    if best_now_fitn > best_fitn_yet or generation_id == 0:
        bestever = best_now
        if current_project.save_best_genome:
            bestever.Save(current_project.seed_save_name + ET.genome_suffix)
        best_ever_gen = generation_id
        best_ever_fitn = best_now_fitn
    print("average fitness            ", av_fitn)
    print("best fitness               ", best_now_fitn)
    print("best fitness ever          ", best_fitn_yet)
    #    http://stackoverflow.com/questions/4098131/how-to-update-a-plot-in-matplotlib
    viz.av_fitn_history.append(av_fitn)
    viz.gen_history.append(generation_id)
    viz.best_fitn_history.append(best_now_fitn)
    n_clients = len(evo_clients)
    last_pop_size = 0
    for genome in genome_list:
        if genome.IsEvaluated():
            last_pop_size += 1
    if current_project.start_from_seed:
        show_seed = current_project.seed_load_name
    else:
        show_seed = False
    if current_project.save_best_genome:
        show_bestever = current_project.seed_save_name
    else:
        show_bestever = False
    net_bestever = NeuralNetwork()  # create Networks to display
    net_bestnow = NeuralNetwork()
    bestever.BuildPhenotype(net_bestever)
    best_now.BuildPhenotype(net_bestnow)
    if current_project.mpl_monitor:
        try:
            visualize.draw_plot(current_project.exp_title, current_project.exp_subtitle, show_seed, show_bestever,
                                viz.start_time_n_date,
                                last_pop_size, pop.Parameters.PopulationSize, n_clients,
                                n_clients_online, viz.fig, viz.best_fitn_history, viz.av_fitn_history,
                                viz.gen_history, best_ever_gen, best_ever_fitn, net_bestever, net_bestnow)
        except Exception as e:
            print('visualisation failed')
            print(e)
        visualize.save_plot_to_pdf(viz.fig, current_project.pdf_filename)

    # work the evo magic
    pop.Epoch()

    pop.Save(current_project.path_to_gene_pool + "population.pop")

    time.sleep(0.5)
    # this is needed to make sure on the clients' side, MNPluginSimFinished()
    # cleared the signals before the next launch trigger is sent


# Script Entry Point
if __name__ == "__main__":
    main()


