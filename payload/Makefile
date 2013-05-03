PSD_PACKAGE=PSDCode

setupstart: setup_hrmc

setupdone:
	@sh ./setupdone.sh 

setup_hrmc:
	@sh ./setuphrmc.sh >& setup.output &

startrun: psd_run_setup run_hrmc

run_hrmc:
	@cd AEAO_v1_1 ; ./HRMC >& output &  echo "$$!" > "run.pid"

psd_run_setup:
	rm -f $(PSD_PACKAGE)/run.pid

run_psd:
	rm -f $(PSD_PACKAGE)/hrmc*
	cp -f AEAO_v1_1/hrmc[0-9]* $(PSD_PACKAGE)/
	rm $(PSD_PACKAGE)/hrmc*.out
	cp -f $(PSD_PACKAGE)/hrmc*.xyz $(PSD_PACKAGE)/hrmc01.xyz
	cd $(PSD_PACKAGE); ./PSD >& psd_output &  echo "$$!" > "run.pid"

running:
	@sh ./running.sh
	
