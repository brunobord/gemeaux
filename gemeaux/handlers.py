from os.path import abspath, isdir, isfile, join

from .exceptions import ImproperlyConfigured
from .responses import (
    DirectoryListingResponse,
    DocumentResponse,
    RedirectResponse,
    TemplateResponse,
)


class Handler:
    def __init__(self, *args, **kwargs):
        pass

    def get_response(self, *args, **kwargs):
        raise NotImplementedError

    def handle(self, url, path, query):
        """
        Handle the request to return the appropriate response.

        Override/write this method if you need extra processing before returning the
        standard Response.
        """
        response = self.get_response(url, path)
        return response


class StaticHandler(Handler):
    """
    Handler for serving static Gemini pages from a directory on your filesystem.
    """

    def __init__(self, static_dir, directory_listing=True, index_file="index.gmi"):
        self.static_dir = abspath(static_dir)
        if not isdir(self.static_dir):
            raise ImproperlyConfigured(f"{self.static_dir} is not a directory")
        self.directory_listing = directory_listing
        self.index_file = index_file

    def __repr__(self):
        return f"<StaticHandler: {self.static_dir}>"

    def get_response(self, url, path):
        """
        Return the static page response according to the configuration & file tree.

        * If the path is a file -> return DocumentResponse for this file.
        * If the path is a directory -> search for "index_file"
          * If index is found => DocumentResponse
          * If not found, depending on the directory_listing arg:
            * If activated, it'll return the DirectoryListingResponse
            * If deactivated => raises a FileNotFoundError.
        * If none of the cases above is satisfied, it raises a FileNotFoundError
        """
        # A bit paranoid…
        if path.startswith(url):
            path = path[len(url) :]
        if path.startswith("/"):  # Should be a relative path
            path = path[1:]

        full_path = join(self.static_dir, path)
        # print(f"StaticHandler: path='{full_path}'")
        # The path leads to a directory
        if isdir(full_path):
            # Directory. Redirect if not root?
            if path and not path.endswith("/"):
                return RedirectResponse(f"{path}/")
            # Directory -> index?
            index_path = join(full_path, self.index_file)
            if isfile(index_path):
                return DocumentResponse(index_path, self.static_dir)
            elif self.directory_listing:
                return DirectoryListingResponse(full_path, self.static_dir)
        # The path is a file
        elif isfile(full_path):
            return DocumentResponse(full_path, self.static_dir)
        # Else, not found or error
        raise FileNotFoundError("Path not found")


class TemplateHandler(Handler):
    """
    Template Handler
    """

    template_file = None

    def get_response(self, url, path):
        """
        Feeds the context variable into the template file to return dynamic content.
        """
        context = self.get_context()
        return TemplateResponse(self.get_template_file(), **context)

    def get_context(self):
        """
        Return a dictionary containing context variables to inject into the template.

        Override this method to inject your dynamic content.
        """
        return {}

    def get_template_file(self):
        """
        Return the path to the template file to use with the `TemplateResponse`.

        You can either define a `template_file` class property or overwrite this method to return the appropriate template.
        """
        if self.template_file:
            return self.template_file
        raise NotImplementedError(
            "Implement a `get_template_file` method or define a `template_file` class attribute"
        )
