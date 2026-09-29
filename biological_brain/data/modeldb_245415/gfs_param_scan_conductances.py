"""
(C) Asaph Zylbertal 2017, HUJI, Jerusalem, Israel

GFS latency as a function of gap junction conductance and 1) voltage gated sodium conductance, 2) voltage gated potassium conductance
3) leak conductance

****************

"""

import neuron
import gfpn
import numpy as np
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['svg.fonttype'] = 'none'

neuron.load_mechanisms('./channels')
           
cv=neuron.h.CVode()
cv.active(1)

g = gfpn.gfs()
g.wire_cells()

ranges={}
ranges['g_gap'] = np.arange(20, 160, 10)
ranges['gnatbar'] = np.arange(230e-3, 530e-3, 20e-3)
ranges['gkbar'] = np.arange(1e-3, 25e-3, 1e-3)
ranges['gleak'] = np.arange(0, 100e-6, 5e-6)
ranges['TTMn_lat_L'] = np.arange(0.1, 45, 3)
ranges['TTMn_med_L'] = np.arange(0.1, 80, 3)
ranges['TTMn_syn_post_loc'] = np.arange(0, 1, 0.1)
ranges['TTMn_diam'] = np.arange(0.5, 10, 0.5)


original_ttmn_delay = 0.926
original_dlmn_delay = 1.44
old_g_gap = 34.5
ttmn_margin = [original_ttmn_delay * 0.99, original_ttmn_delay * 1.01]
dlmn_margin = [original_dlmn_delay * 0.99, original_dlmn_delay * 1.01]

max_ttmn = [1.12, 1.12, 1.12]
max_dlmn = [1.75, 2, 1.75]

param1 = 'g_gap'
param2s = ['gnatbar', 'gkbar', 'gleak']
fig1 = plt.figure()

ii = 1
for p2 in param2s:
    plt.subplot(2, 3, ii)
    param2 = p2
    
    x_young = g.params[param2]
    y_young = g.params[param1]
    y_old = old_g_gap
    
    x_young = (double(len(ranges[param2])) - 1.) * (x_young - ranges[param2][0]) / (ranges[param2][-1] - ranges[param2][0])
    y_young = (double(len(ranges[param1])) - 1.) * (y_young - ranges[param1][0]) / (ranges[param1][-1] - ranges[param1][0])
    y_old = (double(len(ranges[param1])) - 1.) * (y_old - ranges[param1][0]) / (ranges[param1][-1] - ranges[param1][0])
    
    
    delay_dict = g.param_mesh(param1, ranges[param1], param2, ranges[param2])
    delay_dict['DLMn_delays'][delay_dict['DLMn_delays']==-1] = nan
    delay_dict['TTMn_delays'][delay_dict['TTMn_delays']==-1] = nan
    
    
    tcks = np.linspace(np.min(delay_dict['TTMn_delays']), np.max(delay_dict['TTMn_delays']), 20)
    tck_lbls = tcks
    f1 = plt.gca()
    f1.set_xticks(range(0, len(ranges[param2]), 5))
    f1.set_yticks(range(0, len(ranges[param1]), 5))
    f1.set_xticklabels(ranges[param2][::5]*1e3)
    f1.set_yticklabels(ranges[param1][::5])
    plt.xlabel(param2 + ' (mS/cm^2)')
    plt.ylabel(param1 + ' (uS)')
    CS = plt.contour(np.log(delay_dict['TTMn_delays']), 25)
    CS.levels = np.exp(CS.levels)
    CS.levels = CS.levels[CS.levels<max_ttmn[ii-1]]
    plt.clabel(CS, inline=1, inline_spacing=1, use_clabeltext=True, fontsize=9)
   
    plt.contour(delay_dict['TTMn_delays'], levels = ttmn_margin, colors='r', linestyles='dashed')
    
    
    plt.scatter([x_young], [y_young])
    plt.scatter([x_young], [y_old])
    
    plt.subplot(2, 3, ii + 3)
    tcks = np.linspace(np.min(delay_dict['DLMn_delays']), np.max(delay_dict['DLMn_delays']), 20)
    tck_lbls = tcks
    f2 = plt.gca()
    f2.set_xticks(range(0, len(ranges[param2]), 5))
    f2.set_yticks(range(0, len(ranges[param1]), 5))
    f2.set_xticklabels(ranges[param2][::5]*1e3)
    f2.set_yticklabels(ranges[param1][::5])
    plt.xlabel(param2 + ' (mS/cm^2)')
    plt.ylabel(param1 + ' (uS)')
    CS = plt.contour(np.log(delay_dict['DLMn_delays']), 25)
    CS.levels = np.exp(CS.levels)
    CS.levels = CS.levels[CS.levels<max_dlmn[ii-1]]
           
    plt.clabel(CS, inline=1, inline_spacing=1, use_clabeltext=True, fontsize=9)
    plt.contour(delay_dict['DLMn_delays'], levels = dlmn_margin, colors='r', linestyles='dashed')
    
    plt.scatter([x_young], [y_young])
    plt.scatter([x_young], [y_old])

    ii += 1