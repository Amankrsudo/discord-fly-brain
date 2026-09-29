"""
(C) Asaph Zylbertal 2017, HUJI, Jerusalem, Israel

GFS model construction and utilities

****************

"""
import neuron
import numpy as np
from numpy import nan

class gfs(object):

    def __init__(self, params = 'def'):
        if params == 'def':
            self.params={'GF_diam': 8,
                 'GF_L': 400,
                 'TTMn_diam': 6,
                 'TTMn_L': 50,
                 'TTMn_med_L': 60,
                 'TTMn_lat_L': 30,
                 'PSI_diam': 4.5,
                 'PSI_L': 90,
                 'PSI_pas_L': 170,
                 'DLMn_diam_start': 2,
                 'DLMn_diam_end': 4,
                 'DLMn_L': 50,
                 'DLMn_pas_L': 100,
                 'temp': 25.0,
                 'g_gap': 135.0,
                 'TTMn_syn_tau1': 0.5,
                 'TTMn_syn_tau2': 5.0,
                 'TTMn_syn_e': 0,    
                 'TTMn_syn_pre_loc': 1.0,    
                 'TTMn_syn_post_loc': 0.2,
                 'PSI_syn_tau1': 0.1,
                 'PSI_syn_tau2': 5.0,
                 'PSI_syn_e': 0,
                 'PSI_syn_pre_loc': 0.9,
                 'PSI_syn_post_loc': 0.5,
                 'DLMn_syn_tau1': 0.1,
                 'DLMn_syn_tau2': 1.0,
                 'DLMn_syn_e': 0,
                 'DLMn_syn_pre_loc': 0.85,
                 'DLMn_syn_post_loc': 0.25,
                 'GF_TTMn_delay': 1,
                 'GF_TTMn_wt': 0.00,
                 'GF_PSI_delay': 1,
                 'GF_PSI_wt': 0.00,
                 'PSI_DLMn_delay': 0.15,
                 'PSI_DLMn_wt': 0.08,
                 'gnatbar': 300e-3,
                 'gnapbar': 110e-6,
                 'gkbar': 10e-3,
                 'gleak': 30e-6,
                 'Eleak': -85.0,
                 'ena': 65,
                 'ek': -74,
                 'stim_loc': 0.0,
                 'stim_dur': 0.03,
                 'stim_delay': 100,
                 'stim_amp':120.0,
                 'muscle_delay':0.35}
        else:
            self.params = params;
            
        params = self.params
        
        self.GF = neuron.h.Section(name = 'GF');
        self.GF.nseg = 51
        self.GF.diam = params['GF_diam'];
        self.GF.L = params['GF_L'];
        
        self.TTMn = neuron.h.Section(name = 'TTMn');
        self.TTMn.nseg = 51
        self.TTMn.diam = params['TTMn_diam'];
        self.TTMn.L = params['TTMn_L'];
    
        self.TTMn_med = neuron.h.Section(name = 'TTMn_med');
        self.TTMn_med.nseg = 51
        self.TTMn_med.diam = params['TTMn_diam'];
        self.TTMn_med.L = params['TTMn_med_L'];
        self.TTMn_syn = neuron.h.Exp2Syn(self.TTMn_med(params['TTMn_syn_post_loc']))
        self.TTMn_syn.tau1 = params['TTMn_syn_tau1'];
        self.TTMn_syn.tau2 = params['TTMn_syn_tau2'];
        self.TTMn_syn.e = params['TTMn_syn_e'];
        self.TTMn_med.connect(self.TTMn,0,0)

        self.TTMn_lat = neuron.h.Section(name = 'TTMn_lat');
        self.TTMn_lat.nseg = 51
        self.TTMn_lat.diam = params['TTMn_diam'];
        self.TTMn_lat.L = params['TTMn_lat_L'];
        self.TTMn_lat.connect(self.TTMn,0,0)

        self.PSI = neuron.h.Section(name = 'PSI');
        self.PSI.nseg = 51
        self.PSI.diam = params['PSI_diam'];
        self.PSI.L = params['PSI_L'];
        self.PSI_syn = neuron.h.Exp2Syn(self.PSI(params['PSI_syn_post_loc']))
        self.PSI_syn.tau1 = params['PSI_syn_tau1'];
        self.PSI_syn.tau2 = params['PSI_syn_tau2'];
        self.PSI_syn.e = params['PSI_syn_e'];
    
        self.PSI_pas = neuron.h.Section(name = 'PSI_pas');
        self.PSI_pas.nseg = 51
        self.PSI_pas.diam = params['PSI_diam'];
        self.PSI_pas.L = params['PSI_pas_L'];
        self.PSI_pas.connect(self.PSI,0,0)
        
        self.DLMn = neuron.h.Section(name = 'DLMn');
        self.DLMn.nseg = 51
        for seg in self.DLMn:
            seg.diam = params['DLMn_diam_start'] + seg.x * (params['DLMn_diam_end'] - params['DLMn_diam_start'])
    
        self.DLMn.L = params['DLMn_L'];
        self.DLMn_syn = neuron.h.Exp2Syn(self.DLMn(params['DLMn_syn_post_loc']))
        self.DLMn_syn.tau1 = params['DLMn_syn_tau1'];
        self.DLMn_syn.tau2 = params['DLMn_syn_tau2'];
        self.DLMn_syn.e = params['DLMn_syn_e'];

        self.DLMn_pas = neuron.h.Section(name = 'DLMn_pas');
        self.DLMn_pas.nseg = 51
        self.DLMn_pas.diam = params['DLMn_diam_start'];
        self.DLMn_pas.L = params['DLMn_pas_L'];
        self.DLMn_pas.connect(self.DLMn,0,0)

        for cell in [self.PSI_pas, self.TTMn_med, self.TTMn_lat, self.DLMn_pas]:
            cell.insert('pas')
            cell.e_pas = params['Eleak']
            cell.g_pas = params['gleak']
            
        for cell in [self.GF, self.PSI, self.DLMn, self.TTMn]:
            cell.insert('nat')
            cell.insert('nap')
            cell.insert('k')
            cell.insert('pas')
            cell.e_pas = params['Eleak']
            cell.g_pas = params['gleak']
            cell.ena = params['ena']
            cell.ek = params['ek']
            cell.gbar_nat = params['gnatbar']
            cell.gbar_nap = params['gnapbar']
            cell.gbar_k = params['gkbar']
            
        neuron.h.celsius = params['temp']
    
        
        self.vrec = {}
        for nrn in [self.GF, self.TTMn, self.PSI, self.DLMn]:
            self.vrec[nrn.name()] = []
            for seg in nrn:
                self.vrec[nrn.name()].append(neuron.h.Vector())
                self.vrec[nrn.name()][-1].record(seg._ref_v)
            
        self.t = neuron.h.Vector()
        self.t.record(neuron.h._ref_t)
        self.stim = neuron.h.IClamp(self.GF(params['stim_loc']))
        self.stim.dur = params['stim_dur']
        self.stim.delay = params['stim_delay']
        self.stim.amp = params['stim_amp']
        
    def wire_cells(self):
        params = self.params
        self.GF_TTMn_con = neuron.h.NetCon(self.GF(params['TTMn_syn_pre_loc'])._ref_v, self.TTMn_syn, 0, self.params['GF_TTMn_delay'], self.params['GF_TTMn_wt'], sec = self.GF)
        self.GF_PSI_con = neuron.h.NetCon(self.GF(params['PSI_syn_pre_loc'])._ref_v, self.PSI_syn, 0, self.params['GF_PSI_delay'], self.params['GF_PSI_wt'], sec = self.GF)
        self.PSI_DLMn_con = neuron.h.NetCon(self.PSI(params['DLMn_syn_pre_loc'])._ref_v, self.DLMn_syn, 0, self.params['PSI_DLMn_delay'], self.params['PSI_DLMn_wt'], sec = self.PSI)
        
        self.GF_TTMn_gap = neuron.h.gap2(self.TTMn_med(params['TTMn_syn_post_loc']))
        neuron.h.setpointer(self.GF(params['TTMn_syn_pre_loc'])._ref_v, 'vgap', self.GF_TTMn_gap)
        self.GF_TTMn_gap.g = params['g_gap']
        
        self.GF_PSI_gap = neuron.h.gap2(self.PSI(params['PSI_syn_post_loc']))
        neuron.h.setpointer(self.GF(params['PSI_syn_pre_loc'])._ref_v, 'vgap', self.GF_PSI_gap)
        self.GF_PSI_gap.g = params['g_gap']
        
  
    def param_mesh(self, param1, vals1, param2, vals2):
        TTMn_delays = np.zeros((len(vals1), len(vals2)))
        DLMn_delays = np.zeros((len(vals1), len(vals2)))
        total_runs = len(vals1) * len(vals2)
        this_run = 1;
        for p1 in range(len(vals1)):
            for p2 in range(len(vals2)):
                print('Run ' + str(this_run) + ' out of ' + str(total_runs))
                this_run += 1
                self.set_param(param1, vals1[p1])
                self.set_param(param2, vals2[p2])
                neuron.h.finitialize(-65)
                neuron.run(150)
                TTMn_delays[p1, p2] = self.get_delay('TTMn')
                DLMn_delays[p1, p2] = self.get_delay('DLMn')
        self.set_param(param1, self.params[param1])
        self.set_param(param2, self.params[param2])
        return {'TTMn_delays':TTMn_delays, 'DLMn_delays':DLMn_delays}
    
    def set_param(self, param, val):
        if param == 'g_gap':
            for gp in [self.GF_TTMn_gap, self.GF_PSI_gap]:
                gp.g = val
        if param == 'gnatbar':
            for cell in [self.GF, self.PSI, self.DLMn, self.TTMn]:
                cell.gbar_nat = val
        if param == 'gkbar':
            for cell in [self.GF, self.PSI, self.DLMn, self.TTMn]:
                cell.gbar_k = val
        if param == 'gleak':
            for cell in [self.GF, self.TTMn, self.PSI, self.DLMn, self.PSI_pas, self.TTMn_med, self.TTMn_lat, self.DLMn_pas]:
                cell.g_pas = val
        if param == 'GF_diam':
            self.GF.diam = val
        if param == 'GF_L':
            self.GF.L = val
        if param == 'TTMn_L':
            self.TTMn.L = val
        if param == 'DLMn_L':
            self.DLMn.L = val
        if param == 'DLMn_pas_L':
            self.DLMn_pas.L = val
        if param == 'PSI_pas_L':
            self.PSI_pas.L = val
        if param == 'TTMn_lat_L':
            self.TTMn_lat.L = val
        if param == 'TTMn_med_L':
            self.TTMn_med.L = val
        if param == 'PSI_diam':
            self.PSI.diam = val
        if param == 'TTMn_diam':
            self.TTMn_med.diam = val
            self.TTMn_lat.diam = val
        if param == 'TTMn_syn_post_loc':
            self.TTMn.push()
            self.GF_TTMn_gap.loc(val)
            neuron.h.pop_section()
        if param == 'DLMn_syn_post_loc':
            self.DLMn.push()
            self.DLMn_syn.loc(val)
            neuron.h.pop_section()        
        if param == 'ena':
            for cell in [self.GF, self.PSI, self.DLMn, self.TTMn]:
                cell.ena = val
        if param == 'ek':
            for cell in [self.GF, self.PSI, self.DLMn, self.TTMn]:
                cell.ek = val
        if param == 'PSI_DLMn_wt':
            self.PSI_DLMn_con.weight[0] = val
            
    def get_delay(self, cell, thresh=-30):
        max_v = np.max(np.array(self.vrec[cell][-1]))
        if max_v>thresh:
            return self.params['muscle_delay'] + np.array(self.t)[np.argmax(np.array(self.vrec[cell][-1]))] - self.params['stim_delay']
        else:
            return nan