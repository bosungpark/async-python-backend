test:
	pytest --tb=short

black:
	black -l 86 $$(find * -name '*.py')