"""
Created on Mar 10, 2015
@author: raimund
raimund.krenmueller@iaac.net
"""

from __future__ import print_function
import threading as thrd
import Evo_Tools as ET
import os
import time
from Evo_Project import EvoProject
from MultiNEAT import GetGenomeList, Genome, NeuralNetwork

# Name of project folder to load
project_name = 'balance'

# Project configuration currently being trained
current_project = None

if __name__ == "__main__":

    cwd = os.getcwd()
    print(cwd)

    current_project = EvoProject(project_name)

    ET.kill_clients()
    n_clients_online = 0
    evo_clients = []
    print("initializing evo-network...")
    evo_clients = ET.init_evo_net(ET.evo_client_map, ET.genomes_per_client_each, ET.genomes_per_client_all)
    for client in evo_clients:
        client.reset()
        client.update_status()
        if client.is_online:
            n_clients_online += 1
    if n_clients_online > 0:
        print(len(evo_clients), "client(s) created, ", n_clients_online, "online")
        # Create new randomized genomes
        if not current_project.start_from_seed:
            pop, pop_size_init = ET.init_pop(evo_clients,current_project)
        # Load best genomes from seed file
        else:
            seed_genome = Genome(current_project.seed_load_name + ET.genome_suffix)
            print("starting from seed genome in file", current_project.seed_load_name + ET.genome_suffix, ", genome ID:",
                  seed_genome.GetID())
            pop, pop_size_init = ET.pop_from_seed(evo_clients, seed_genome)
            seed_genome.Save('seed_from' + ET.genome_suffix)
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
        gen_history = []
        av_fitn_history = []
        best_fitn_history = []
        if current_project.start_from_seed:
            show_seed = current_project.seed_load_name
        else:
            show_seed = False
        if current_project.save_best_genome:
            show_bestever = current_project.seed_save_name
        else:
            show_bestever = False
        start_time_n_date = str(time.asctime(time.localtime()))
        if current_project.mpl_monitor:
            import Evo_Visualize as visualize
            fig = visualize.init_plot()

            #    vvv_________________________main generational loop: __________________________vvv
        for generation in range(ET.n_generations):
            if current_project.mpl_monitor:
                visualize.set_timer_starttime('current')
            print("")
            print("___________________ next generation:", generation, "___________________")

            # create and launch initialization threads:
            print('launching evaluations...')
            gene_pool = GetGenomeList(pop)
            init_eval_threads = []
            lock = thrd.RLock()
            for client in evo_clients:
                new_thrd = thrd.Thread(target=ET.init_eval, args=(client, gene_pool, current_project.eval_scene, lock))
                init_eval_threads.append(new_thrd)
                new_thrd.start()
            for thread in init_eval_threads:
                try: thread.join()
                except: pass
            # create and launch monitoring threads
            print('evaluating...')
            monitor_eval_threads = []
            lock = thrd.RLock()
            for client in evo_clients:
                new_thrd = thrd.Thread(target=ET.monitor_eval, args=(client, lock))
                monitor_eval_threads.append(new_thrd)
                new_thrd.start()
            for thread in monitor_eval_threads:
                try: thread.join()
                except: pass

            # all evaluations done, now print some stats & save the best genome
            print('evaluations done.')
            genome_list = GetGenomeList(pop)
            fitn_list = []
            for genome in genome_list:
                fitn_list.append(genome.GetFitness())
            print(fitn_list)
            av_fitn = sum(fitn_list) / float(len(fitn_list))
            best_now = pop.GetBestGenome()  # best of the current generation
            best_now_fitn = best_now.GetFitness()
            best_fitn_yet = pop.GetBestFitnessEver()
            if best_now_fitn > best_fitn_yet or generation == 0:
                bestever = best_now
                if current_project.save_best_genome:
                    bestever.Save(current_project.seed_save_name + ET.genome_suffix)
                best_ever_gen = generation
                best_ever_fitn = best_now_fitn
            print("average fitness            ", av_fitn)
            print("best fitness               ", best_now_fitn)
            print("best fitness ever          ", best_fitn_yet)
            #    http://stackoverflow.com/questions/4098131/how-to-update-a-plot-in-matplotlib
            av_fitn_history.append(av_fitn)
            gen_history.append(generation)
            best_fitn_history.append(best_now_fitn)
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
                try: visualize.draw_plot(current_project.exp_title, current_project.exp_subtitle, show_seed, show_bestever, start_time_n_date,
                                    last_pop_size, pop_size_init, n_clients,
                                    n_clients_online, fig, best_fitn_history, av_fitn_history,
                                    gen_history, best_ever_gen, best_ever_fitn, net_bestever, net_bestnow)
                except: print('visualisation failed')
                visualize.save_plot_to_pdf(fig, current_project.pdf_filename)

            # work the evo magic
            pop.Epoch()

            time.sleep(0.5)
            # this is needed to make sure on the clients' side, MNPluginSimFinished()
            # cleared the signals before the next launch trigger is sent

        #   ^^^________end - main generational loop____^^^

        for client in evo_clients:
            if client.is_online:
                client.end()

    else:
        print("no clients online")
    print("program ended")



