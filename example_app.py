from gemeaux import App
from gemeaux.handlers import Handler, StaticHandler
from gemeaux.responses import (
    InputResponse,
    NotFoundResponse,
    PermanentRedirectResponse,
    RedirectResponse,
    SensitiveInputResponse,
    TextResponse,
)


class HelloWorldHandler(Handler):
    """
    Proof-of-concept dynamic handler
    """

    def get_response(self):
        return TextResponse("Title", "Hello World!")

    def handle(self, url, path):
        response = self.get_response()
        return response


if __name__ == "__main__":
    urls = {
        "": StaticHandler(
            # Static pages, with directory listing
            static_dir="examples/static/",
            directory_listing=True,
        ),
        "/test": StaticHandler(
            # Static pages, no directory listing
            static_dir="examples/static/",
            directory_listing=False,
        ),
        "/with-sub": StaticHandler(
            # Static pages, pointing at a "deep" directory with an index.gmi file
            static_dir="examples/static/sub-dir",
        ),
        "/index-file": StaticHandler(
            # Static pages, pointing at a directory with an alternate index file
            static_dir="examples/static/empty-dir",
            index_file="one.gmi",
        ),
        # Custom Handler
        "/hello": HelloWorldHandler(),
        # Direct response
        "/direct": TextResponse(title="Direct Response", body="I am here"),
        # Standard responses
        "/10": InputResponse(prompt="What's the ultimate answer?"),
        "/11": SensitiveInputResponse(prompt="What's the ultimate answer?"),
        "/30": RedirectResponse(target="/hello"),
        "/31": PermanentRedirectResponse(target="/hello"),
        # TODO: 40 TEMPORARY FAILURE
        # TODO: 41 SERVER UNAVAILABLE
        # TODO: 42 (?) CGI ERROR
        # TODO: 43 (?) PROXY ERROR
        # TODO: 44 SLOW DOWN
        # TODO: 50 PERMANENT FAILURE
        # TODO: 51 NOT FOUND (already covered by other response, but nice to have)
        "/51": NotFoundResponse("Nobody will escape the Area 51"),
        # TODO: 52 GONE
        # TODO: 53 ? PROXY REQUEST REFUSED
        # TODO: 59 BAD REQUEST
        # TODO: 60 (?) CLIENT CERTIFICATE REQUIRED
        # TODO: 61 (?) CERTIFICATE NOT AUTHORISED
        # TODO: 62 (?) CERTIFICATE NOT VALID
        # Configration errors. Uncomment to see how they're handled
        # "error": "I am an error",
        # "error": StaticHandler(static_dir="/tmp/not-a-directory"),
    }
    app = App(urls)
    app.run()
