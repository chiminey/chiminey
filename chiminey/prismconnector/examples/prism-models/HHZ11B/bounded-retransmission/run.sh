#prism  brp.nm brp.pctl -param pL=0.2:0.3,pK=0.8:0.9
#prism brp.nm brp.pctl -const N=64,MAX=5 -param pL,pK -parambisim weak

#prism brp.nm brp.pctl -const N=64,MAX=5 -param pL,pK > output_64_5.txt
#prism brp.nm brp.pctl -const N=64,MAX=5 -param pL,pK -parambisim weak > output_64_5_weak.txt

prism brp.nm brp.pctl -const N=256,MAX=4 -param pL,pK > output_256_4.txt
#prism brp.nm brp.pctl -const N=256,MAX=4 -param pL,pK -parambisim weak > output_256_4_weak.txt

#prism brp.nm brp.pctl -const N=256,MAX=5 -param pL,pK > output_256_4.txt
#prism brp.nm brp.pctl -const N=256,MAX=5 -param pL,pK -parambisim weak > output_256_5_weak.txt
