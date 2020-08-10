import requests

def make_source(type, id):
    if type == "relmon":
        return ReleaseMonitoring(type, id)
    if type == "npm":
        return NPM(type, id)
    raise Exception("No such source.")

class Source:
    """A place to pull version numbers from."""

    data = None

    def __init__(self, type: str, id: str):
        """Create a source."""
        self.type = type
        self.id = id

    def refresh_source(self) -> None:
        return None
    
    def get_latest(self) -> str:
        """Get the latest version of a piece of software."""
        raise Exception("get_latest() called on parent Source class")

    def get_project_page(self) -> str:
        """Get the project homepage URL for a piece of software."""
        raise Exception("get_project_page() called on parent Source class")

    def get_all_versions(self) -> list:
        """Get a list of all versions for a piece of software."""
        raise Exception("get_all_versions() called on parent Source class")


class ReleaseMonitoring(Source):
    """The release-monitoring.org source, implements many other sources."""

    def __init__(self, type, id):
        assert type == "relmon"
        Source.__init__(self, type, id)

    def refresh_source(self) -> None:
        resp = requests.get(f'https://release-monitoring.org/api/project/{self.id}')
        if resp.status_code != 200:
            raise Exception('release-monitoring did not 200', resp.status_code)
        self.data = resp.json()
    
    def get_latest(self) -> str:
        """Get the latest version of a piece of software."""
        return self.data["version"]
    
    def get_project_page(self) -> str:
        """Get the project homepage URL for a piece of software."""
        return self.data["homepage"]

    def get_all_versions(self) -> list:
        """Get a list of all versions for a piece of software."""
        return self.data["versions"]


class NPM(Source):
    """The npmjs.org source, for JavaScript packages."""

    def __init__(self, type, id):
        assert type == "npm"
        Source.__init__(self, type, id)

    def refresh_source(self) -> None:
        resp = requests.get(f'https://registry.npmjs.org/{self.id}')
        if resp.status_code != 200:
            raise Exception('npm did not 200', resp.status_code)
        self.data = resp.json()
    
    def get_latest(self) -> str:
        """Get the latest version of a piece of software."""
        return self.data["dist-tags"]["latest"]
    
    def get_project_page(self) -> str:
        """Get the project homepage URL for a piece of software."""
        return self.data["homepage"]

    def get_all_versions(self) -> list:
        """Get a list of all versions for a piece of software."""
        return [x for x in self.data["versions"]]
