"""
Created on Jun 8, 2015
@author: raimund
raimund.krenmueller@iaac.net
"""

import sys
sys.ps1 = 'workaround'
import matplotlib
import cv2
import time
# u'pgf', u'cairo', u'MacOSX', u'CocoaAgg',
# u'gdk', u'ps', u'GTKAgg', u'nbAgg', u'GTK', u'Qt5Agg', u'template', u'emf',
# u'GTK3Cairo', u'GTK3Agg', u'WX', u'Qt4Agg', u'TkAgg', u'agg', u'svg', u'GTKCairo', u'WXAgg', u'WebAgg', u'pdf'
from matplotlib.backends.backend_pdf import PdfPages

import matplotlib.pyplot as plt
import numpy as np
from MultiNEAT import DrawPhenotype

timer_start_time = {}  # global dict for start_times


def save_plot_to_pdf(fig, filename):
    pp = PdfPages(filename)
    pp.savefig(fig,facecolor = (0.7, 0.7, 0.7)) # Force background color
    pp.close()


def format_time_hms(raw_time):
    hours, remainder = divmod(raw_time, 3600)
    if hours == 0:
        h_display = ''
    else:
        h_display = str(int(hours)) + 'h'
    minutes, seconds = divmod(remainder, 60)
    if minutes == 0:
        m_display = ''
    else:
        m_display = str(int(minutes)) + 'm'
    formatted_time = (h_display + m_display + str(round(seconds, 1)) + 's')
    return formatted_time


def set_timer_starttime(timer_name):
    timer_start_time[timer_name] = time.time()


def timer_callback(text_current, text_total, fig):  # callback function for timer object
    now = time.time()
    # print '.'
    elapsed_current = (now - timer_start_time['current'])
    elapsed_current_str = 'CURRENT: ' + format_time_hms(elapsed_current)
    text_current.set_text(elapsed_current_str)
    elapsed_total = + (now - timer_start_time['total'])
    elapsed_total_str = 'TOTAL: ' + format_time_hms(elapsed_total)
    text_total.set_text(elapsed_total_str)
    # fig.canvas.draw()
    # fig.show()
    # plt.draw()
    # plt.show(block = False)


def init_plot():
    # http://www.randalolson.com/2014/06/28/how-to-make-beautiful-data-visualizations-in-python-with-matplotlib/
    # plt.ion()
    plt.ioff()
    col_canvas = (0.7, 0.7, 0.7)
    col_window = col_canvas
    col_spines = (0.97, 0.97, 0.97)
    col_title = (1, 1, 1)
    col_ticks = col_spines
    # manager = backend.new_figure_manager(0)
    frame_settings = matplotlib.figure.SubplotParams(left=0.1, bottom=0.1, right=0.98, top=0.85, wspace=0.4, hspace=0)
    fig = plt.figure('EVO_NET MONITOR', facecolor=col_window, frameon=True, subplotpars=frame_settings, dpi=80,
                     figsize=(20, 10))
    gs = matplotlib.gridspec.GridSpec(2, 2, width_ratios=[4, 2])
    ax = fig.add_subplot(gs[:, 0], facecolor=col_canvas, frameon=True)
    ax2 = fig.add_subplot(gs[1], facecolor=col_canvas, frameon=True)
    ax3 = fig.add_subplot(gs[3], facecolor=col_canvas, frameon=True)
    ax.spines['bottom'].set_color(col_spines)
    ax.spines['left'].set_color(col_spines)
    ax.spines['right'].set_color(col_spines)
    ax.tick_params(axis='x', colors=col_spines, width=1)
    ax.tick_params(axis='y', colors=col_spines, width=1)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.set_xticklabels([])
    ax.set_yticklabels([])
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    ax2.spines['left'].set_visible(False)
    ax2.spines['bottom'].set_visible(False)
    ax2.set_xticklabels([])
    ax2.set_yticklabels([])
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    ax3.spines['left'].set_visible(False)
    ax3.spines['bottom'].set_visible(False)
    ax3.set_xticklabels([])
    ax3.set_yticklabels([])

    set_timer_starttime('total')
    # timer = fig.canvas.new_timer(interval=10)

    # args = [timer_current_text, timer_total_text, fig]
    # timer.add_callback(timer_callback, *args) # 1st argument: callback function
    # timer.start()
    return fig


def draw_plot(title_text, title2_text, seed, best, start_time_n_date, a_pop_size, a_pop_size_init, a_n_clients,
              a_n_clients_online, fig, y1_data, y2_data, x_data, bestever_gen, bestever_val, net_bestever, net_bestnow):
    ax, ax2, ax3 = fig.get_axes()
    col_title = (0.95, 0.95, 0.95)
    col_title2 = (1, 1, 1)
    col_annotation = (0.98, 0.98, 0.98)
    col_current = (1, 1, 1)
    col_ax_label = (1, 1, 1)
    col_best = (0.8, 0.5, 0.5)
    col_avrg = (0.5, 0.3, 0.2)
    col_bestever = 'yellow'  # (1,1,0.5)
    col_new_bestever = 'yellow'
    col_bestever_label = (0.8, 0.8, 0.8)
    col_bestever_arrow = (1, 1, 1)
    fs_title = 26
    fs_title2 = 13
    fs_title3 = 10
    x_offs_title = 0
    y_offs_title = 14
    fs_annotation = 20  # values
    x_offs_annotate = 5
    y_offs_annotate = 8
    fs_annotation2 = 10  # text
    y_offs_annotate2 = -12  # text 1 below value
    y_offs_annotate3 = -24  # text below value
    y_offs_annotate4 = -24  # text below value, 2 lines
    fs_axes_labels = 10
    fs_current = 20
    x_pos_anno_best = x_data[-1]
    y_pos_anno_best = y1_data[-1]
    y_offs_annotate_bestever = 40
    x_offs_annotate_bestever = -40
    y_offs_annotate_bestever2 = 18
    y_offs_annotate_bestever3 = -40
    arrow_properties_bestever = dict(arrowstyle='-', linestyle='dotted', color=col_bestever_arrow)

    ax.clear()
    ax2.clear()
    ax.xaxis.set_label_coords(1, 0)
    ax.set_xlabel('LAST GEN', fontsize=fs_axes_labels, color=col_ax_label, ha='right')

    # the actual graphs:
    ax.set_xlim(0, x_data[-1] if x_data[-1] > 0 else 1)
    ax.set_ylim(top=bestever_val * 1.3)
    y_limits = ax.get_ylim()
    x_limits = ax.get_xlim()
    line1, = ax.plot([], [], lw=1.5, color=col_best)
    line2, = ax.plot(x_data, y2_data, linestyle='dotted', lw=1.5, color=col_avrg)
    line1.set_xdata(x_data)
    line1.set_ydata(y1_data)

    # title
    title_anno = ax.annotate(title_text, xy=(0, 1), xycoords='axes fraction',
                             xytext=(x_offs_title, y_offs_title),
                             textcoords='offset points',
                             fontsize=fs_title, color=col_title)

    # eval_scene
    title_info_anno = ax.annotate(title2_text, xy=(0, 1), xycoords='axes fraction',
                                  xytext=(10, 3),
                                  textcoords='offset points',
                                  va='top', ha='left',
                                  fontsize=fs_title3, color=col_title2)

    # seed or not, start time and date, best_ever file   
    if seed:
        seed_text = ', SEED: ' + seed
    else:
        seed_text = ', SEED: none'

    if best:
        save_best_text = 'ALL TIME BEST saved as ' + best
    else:
        save_best_text = 'ALL TIME BEST NOT SAVED! '

    title_info2_anno = ax.annotate('START TIME: ' + start_time_n_date + ' ' + seed_text + '\n' + save_best_text,
                                   xy=(0, 0), xycoords=title_info_anno,
                                   xytext=(0, -3),
                                   textcoords='offset points',
                                   va='top', ha='left',
                                   fontsize=fs_title3, color=col_title2)

    # always annotate average of last generation:
    x_pos_anno_avrg = x_data[-1]
    y_pos_anno_avrg = y2_data[-1]
    '''     
    anno_avrg1 = ax.annotate(str(round(y2_data[-1],2)), xy = (x_pos_anno_avrg, y_pos_anno_avrg),
                  xytext = (x_offs_annotate, y_offs_annotate),
                  textcoords = 'offset points',
                  fontsize = fs_annotation, color = col_avrg)  
                  
    '''
    anno_avrg2 = ax.annotate('AVRG', xy=(x_pos_anno_avrg, y_pos_anno_avrg),
                             xytext=(x_offs_annotate, y_offs_annotate + y_offs_annotate2),
                             textcoords='offset points',
                             fontsize=fs_annotation2, color=col_avrg)

    anno_avrg1 = ax.annotate('', xy=(0, 0),
                             xytext=(0, 0),
                             textcoords='offset points',
                             fontsize=fs_annotation, color=col_avrg)

    anno_avrg1.set_text(str(round(y2_data[-1], 2)))
    anno_avrg1.xy = (x_pos_anno_avrg, y_pos_anno_avrg)
    anno_avrg1.xyann = (x_offs_annotate, y_offs_annotate)

    bestever_age = x_data[-1] - bestever_gen
    if bestever_age == 0:
        # a new champion:
        ax.annotate('BEST', xy=(x_pos_anno_best, y_pos_anno_best),
                    xytext=(x_offs_annotate, y_offs_annotate + y_offs_annotate2),
                    textcoords='offset points',
                    fontsize=fs_annotation2, color=col_best)
        ax.annotate(str(round(y1_data[-1], 2)), xy=(x_pos_anno_best, y_pos_anno_best),
                    xytext=(x_offs_annotate, y_offs_annotate), textcoords='offset points',
                    fontsize=fs_annotation, color=col_bestever)

    else:
        # annotate best_ever
        ax.annotate(str(round(bestever_val, 2)), xy=(bestever_gen, bestever_val),
                    xytext=(x_offs_annotate_bestever, y_offs_annotate_bestever),
                    textcoords='offset points',
                    fontsize=fs_annotation, color=col_bestever)
        ax.annotate('gen ' + str(bestever_gen) + '\n' + '(' + str(bestever_age) + ' ago)',
                    xy=(bestever_gen, bestever_val),
                    xytext=(x_offs_annotate_bestever,
                            y_offs_annotate_bestever + y_offs_annotate_bestever2 + y_offs_annotate_bestever3),
                    textcoords='offset points',
                    fontsize=fs_annotation2, color=col_annotation, arrowprops=arrow_properties_bestever)

        # and annotate best in last generation with % of best ever:
        if bestever_val > 0:
            dist_to_champ = round((y1_data[-1] / (bestever_val / 100)) - 100, 2)
        else:
            dist_to_champ = 0
        ax.annotate('BEST', xy=(x_pos_anno_best, y_pos_anno_best),
                    xytext=(x_offs_annotate, y_offs_annotate + y_offs_annotate2),
                    textcoords='offset points',
                    fontsize=fs_annotation2, color=col_best)
        ax.annotate(str(round(y1_data[-1], 2)), xy=(x_pos_anno_best, y_pos_anno_best),
                    xytext=(x_offs_annotate, y_offs_annotate), textcoords='offset points',
                    fontsize=fs_annotation, color=col_best)
        ax.annotate('(' + str(dist_to_champ) + ' %)', xy=(x_pos_anno_best, y_pos_anno_best),
                    xytext=(x_offs_annotate, y_offs_annotate + y_offs_annotate3),
                    textcoords='offset points',
                    fontsize=fs_annotation2, color=col_annotation)

    # show last generation number 
    now = time.time()
    elapsed_current = (now - timer_start_time['current'])
    elapsed_current_str = format_time_hms(elapsed_current)

    gen_text = ax.annotate(str(x_data[-1]), xy=(x_limits[1], y_limits[0]),
                           xytext=(5, -15),
                           textcoords='offset points',
                           fontsize=fs_annotation, color=col_current)
    # time
    col_timer = (0.95, 0.95, 0.95)
    elapsed_total = (now - timer_start_time['total'])
    elapsed_total_str = elapsed_current_str + ', TOTAL: ' + format_time_hms(elapsed_total)
    timer_total_text = ax.annotate(elapsed_total_str, xy=(1, 0), xycoords=gen_text,
                                   xytext=(10, 0),
                                   textcoords='offset points',
                                   fontsize=fs_axes_labels, color=col_timer)

    # show clients
    col_ok = col_annotation
    col_not_ok = (1.0, 0.5, 0.5)
    if a_n_clients_online == a_n_clients:
        col_cli = col_ok
    else:
        col_cli = col_not_ok

    cli_anno1 = ax.annotate('CLI ', xy=(1, 1), xycoords='axes fraction',
                            xytext=(-50, 5),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=fs_annotation2, color=col_annotation)
    cli_anno2 = ax.annotate(str(a_n_clients_online), xy=(1, 0), xycoords=cli_anno1,
                            xytext=(0, 0),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=fs_annotation, color=col_annotation)
    cli_anno3 = ax.annotate('(' + str(a_n_clients) + ')', xy=(1, 0), xycoords=cli_anno2,
                            xytext=(1, 0),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=fs_annotation, color=col_cli)

    # show pop
    if a_pop_size == a_pop_size_init:
        col_pop = col_ok
    else:
        col_pop = col_not_ok
    cli_anno1 = ax.annotate('POP ', xy=(1, 0), xycoords=cli_anno3,
                            xytext=(5, 0),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=fs_annotation2, color=col_annotation)
    cli_anno2 = ax.annotate(str(a_pop_size), xy=(1, 0), xycoords=cli_anno1,
                            xytext=(0, 0),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=fs_annotation, color=col_annotation)
    cli_anno3 = ax.annotate('(' + str(a_pop_size_init) + ')', xy=(1, 0), xycoords=cli_anno2,
                            xytext=(1, 0),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=fs_annotation, color=col_cli)

    # set the ticks
    ax.yaxis.set_ticks_position('left')
    xticks = ax.xaxis.get_major_ticks()
    middle_tick = int(len(xticks) / 2)
    for tick in xticks:
        tick.label1.set_visible(False)

    if x_data[-1] > 9:
        xticks[1].label1.set_visible(True)
        xticks[middle_tick].label1.set_visible(True)

    yticks = ax.yaxis.get_major_ticks()
    for tick in yticks[1:-2]:
        tick.set_visible(False)
        tick.label1.set_visible(False)

    # draw NN for best_ever
    ax2.clear()
    width = 1000
    height = 600
    image = np.zeros((height, width, 3), np.uint8)
    image[:, 0:width] = (255 * 0.85, 255 * 0.85, 255 * 0.85)  # grey background
    rect = (0, 0, width, height)
    neuron_circle_dia = 15
    max_line_width = 10
    DrawPhenotype(image, rect, net_bestever, neuron_circle_dia, max_line_width)
    b, g, r = cv2.split(image)  # get b,g,r
    rgb_img = cv2.merge([r, g, b])
    ax2.imshow(rgb_img)
    for tick in ax2.xaxis.get_major_ticks():
        tick.set_visible(False)
    for tick in ax2.yaxis.get_major_ticks():
        tick.set_visible(False)
    NN_anno1 = ax2.annotate('*', xy=(0, 1), xycoords='axes fraction',
                            xytext=(10, -10),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=50, color=col_bestever)

    # draw NN for best_now
    ax3.clear()
    width = 1000
    height = 600
    image2 = np.zeros((height, width, 3), np.uint8)
    image2[:, 0:width] = (255 * 0.85, 255 * 0.85, 255 * 0.85)  # grey background
    rect2 = (0, 0, width, height)
    neuron_circle_dia = 15
    max_line_width = 10
    DrawPhenotype(image2, rect2, net_bestnow, neuron_circle_dia, max_line_width)
    b, g, r = cv2.split(image2)  # get b,g,r
    rgb_img2 = cv2.merge([r, g, b])
    ax3.imshow(rgb_img2)
    for tick in ax3.xaxis.get_major_ticks():
        tick.set_visible(False)
    for tick in ax3.yaxis.get_major_ticks():
        tick.set_visible(False)
    NN_anno1 = ax3.annotate('*', xy=(0, 1), xycoords='axes fraction',
                            xytext=(10, -10),
                            textcoords='offset points',
                            va='bottom', ha='left',
                            fontsize=50, color=col_best)

    # plt.draw()
    fig.canvas.draw()
    fig.show()
    fig.canvas.start_event_loop(0.01)
    # time.sleep(0.05)
