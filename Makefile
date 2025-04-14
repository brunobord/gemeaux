SHELL := /bin/bash

serve:
	python3 example_app.py

cert:
	openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem -subj "/CN=localhost" -newkey rsa:4096 -extensions san -config <(echo '[req]'; echo 'distinguished_name=req'; echo '[san]'; echo 'subjectAltName=DNS:localhost,DNS:127.0.0.1')

# DEV ONLY
lint: isort black flake8

isort:
	isort --profile black .
black:
	black .
flake8:
	flake8 .
