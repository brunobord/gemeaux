serve:
	python3 app.py

cert:
	openssl req -new -x509 -days 365 -nodes -out cert.pem -keyout key.pem -subj "/CN=localhost" -newkey rsa:4096 -addext "subjectAltName = DNS:localhost,DNS:127.0.0.1"

# DEV ONLY
lint: isort black

isort:
	isort --profile black app.py gemeaux/*.py
black:
	black app.py gemeaux/*.py
