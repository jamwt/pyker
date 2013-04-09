from setuptools import setup

setup(
    name='pyker',
	version='0.1a',
	author="Jamie Turner",
#	author_email="jamie-pyker@jamwt.com",
#	url="http://jamwt.com",
#	download_url="http://jamwt.com/downloads/",
#	description="",

#	long_description= ""
	packages=["pyker", "pyker.fe", "pyker.be"],
	scripts=["scripts/pykerd", "scripts/pyker"],
	)
