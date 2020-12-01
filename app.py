from server import App, Handler, StaticHandler, TextResponse


class HelloWorldHandler(Handler):
    def get_response(self):
        return TextResponse("Title", "Hello World!")

    def handle(self, url, path):
        response = self.get_response()
        return response


if __name__ == "__main__":
    config = {
        "ip": "localhost",
        "port": 1965,
        "certfile": "cert.pem",
        "keyfile": "key.pem",
        "urls": {
            "": StaticHandler(static_dir="examples/static/", directory_listing=True),
            "/test": StaticHandler(
                static_dir="examples/static/", directory_listing=False
            ),
            "/with-sub": StaticHandler(
                static_dir="examples/static/sub-dir", directory_listing=True
            ),
            "/hello": HelloWorldHandler(),
        },
    }
    app = App(**config)
    app.run()
