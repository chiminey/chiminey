from setuptools  import setup, find_packages

setup(
    name='cloudenabling',
    version='0.1dev',
    packages=find_packages(),
    license='MIT License',
    long_description=open('README.txt').read(),
    entry_points = {
	'console_scripts': ['mc = mc.p:__main__',]
	}
)
