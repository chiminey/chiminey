#prism zeroconf_p.nm zeroconf_p.pctl -param p=0.2:0.205,q=0.2:0.205 -paramprecision 0.5 -exportresults x.txt:csv
#prism zeroconf.pm zeroconf.pctl -const n=5 -param p,q > output_5.txt
#prism zeroconf.pm zeroconf.pctl -const n=50 -param p,q > output_50.txt
prism zeroconf.pm zeroconf.pctl -const n=100 -param p,q > output_100.txt
#prism zeroconf.pm zeroconf.pctl -const n=140 -param p,q > output_140.txt
