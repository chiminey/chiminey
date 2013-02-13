PSD_PACKAGE=PSDCode

setup: setup_hrmc setup_psd print

setup_hrmc:
	@sudo yum -y install dos2unix
	@sudo yum -y install gcc-gfortran
	@sudo yum -y install compat-gcc-34-g77.x86_64
	@tar --extract --gunzip --verbose --file=aeao_v1_1_package.tar.gz
	@g77 AEAO_v1_1/HRMC.f -o AEAO_v1_1/HRMC

setup_psd:
	@sudo yum -y install unzip;
	@rm -rf $(PSD_PACKAGE)
	@unzip -o PSDCode.zip
	@cd $(PSD_PACKAGE); g77 PSD.f -o PSD

print:
	@echo Setup completed

startrun: psd_run_setup run_hrmc

run_hrmc:
	@cd AEAO_v1_1 ; ./HRMC >& output &  echo "$$!" > "run.pid"

psd_run_setup:
	rm -f $(PSD_PACKAGE)/run.pid
	rm -f $(PSD_PACKAGE)/hrmc*
	rm -f $(PSD_PACKAGE)/psd.dat
	rm -f $(PSD_PACKAGE)/psd_output


run_psd:
	rm -f $(PSD_PACKAGE)/hrmc*
	cp -f AEAO_v1_1/hrmc[0-9]* $(PSD_PACKAGE)/
	rm $(PSD_PACKAGE)/hrmc*.out
	cp -f $(PSD_PACKAGE)/hrmc*.xyz $(PSD_PACKAGE)/hrmc01.xyz
	cd $(PSD_PACKAGE); ./PSD >& psd_output &  echo "$$!" > "run.pid"

running:
	@sh ./running.sh
