COMMENT

k.mod

Potassium channel, Hodgkin-Huxley style kinetics.  
Adapted from Gunay et al., 2015

ENDCOMMENT

INDEPENDENT {t FROM 0 TO 1 WITH 1 (ms)}

NEURON {
	SUFFIX k 
	USEION k READ ek WRITE ik
	RANGE m, gk, gbar, ik
	GLOBAL v1_2m, km
	RANGE minf, mtau
	GLOBAL vmin, vmax
}

PARAMETER {
	gbar = 0   	(S/cm2)	: 0.12 mho/cm2
	
	v1_2m  = -12.85	(mV)		: v 1/2 for act		
	km   = -19.91	(mV)			: act slope		



	v 		(mV)
	dt		(ms)
	celsius		(degC)
	vmin = -120	(mV)
	vmax = 1000	(mV)
	
}


UNITS {
	(mA) = (milliamp)
	(mV) = (millivolt)
	(pS) = (picosiemens)
	(um) = (micron)
} 

ASSIGNED {
	ik 		(mA/cm2)
	gk		(S/cm2)
	ek		(mV)
	minf 		
	mtau 		(ms)	
	
}
 

STATE {m}

INITIAL { 
	trates(v)
	m = minf
}

BREAKPOINT {

	SOLVE states METHOD cnexp
	gk = gbar*m
	ik = gk * (v - ek)
} 


DERIVATIVE states {   :Computes state variables m, h, and n 
        trates(v)      :             at the current v and dt.
        
        m' =  (minf-m)/(mtau)
}

PROCEDURE trates(v) {  
                      
        
    TABLE minf, mtau
	DEPEND  v1_2m, km
	
	FROM vmin TO vmax WITH 1600

	rates(v): not consistently executed from here if usetable == 1


}


PROCEDURE rates(vm) {  

	
	minf = 1/(1+exp((vm-v1_2m)/km))
	mtau = 1
}



