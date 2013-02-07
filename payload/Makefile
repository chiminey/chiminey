setup_hrmc:
	@sudo yum -y install dos2unix
	@sudo yum -y install gcc-gfortran
	@sudo yum -y install compat-gcc-34-g77.x86_64
	@tar --extract --gunzip --verbose --file=aeao_v1_1_package.tar.gz
	@g77 AEAO_v1_1/HRMC.f -o AEAO_v1_1/HRMC

print:
	@echo Hello World
