NEURON {
	
	POINT_PROCESS gap2
	NONSPECIFIC_CURRENT i
	RANGE i, g
	POINTER vgap	


}
PARAMETER {
	v (millivolt)
	g = 0 (nanosiemens) :1 (nanosiemens) : 1nS = 1000 pS
}
ASSIGNED {
	i (nanoamp)
	vgap (millivolt)
}
BREAKPOINT {

	i = (v - vgap)*g*(0.001)
}
