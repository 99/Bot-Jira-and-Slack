.PHONY: clean
clean:
	rm -rf build dist bot.egg-info

.PHONY: run
run: install
	bin/bot

.PHONY: repl
repl: install
	bin/bot -t

.PHONY: requirements
requirements:
	pip install -r requirements.txt

.PHONY: install
install: requirements
	python setup.py install
	make clean

.PHONY: publish
publish:
	pandoc -s -w rst README.md -o README.rs
	python setup.py sdist upload
	rm README.rs
