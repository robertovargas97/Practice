test:
	./manage.py test

keeptest:
	./manage.py test --keepdb

wsdl:
	python -mzeep $(wsdl) > ../docs/inspected_wsdl/$(output).wsdl.txt

.PHONY: test keeptest wsdl
