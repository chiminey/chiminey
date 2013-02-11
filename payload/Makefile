setup: setup_hrmc setup_psd print

setup_hrmc:
	@sudo yum -y install dos2unix
	@sudo yum -y install gcc-gfortran
	@sudo yum -y install compat-gcc-34-g77.x86_64
	@tar --extract --gunzip --verbose --file=aeao_v1_1_package.tar.gz
	@g77 AEAO_v1_1/HRMC.f -o AEAO_v1_1/HRMC

setup_psd:
	@sudo yum -y install unzip
	@unzip -o PSDCode.zip
	@g77 PSD.f -o PSD

print:
	@echo Setup completed

startrun:
	@cd AEAO_v1_1 ; ./HRMC >& output &  echo "$$!" > "run.pid"

running:
	@sh ./running.sh

