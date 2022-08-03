all: repro

env/bin/python: environment.yml
	rm -rf env
	conda env create -f=environment.yml -p env

repro: env/bin/python
	env/bin/python repro.py
