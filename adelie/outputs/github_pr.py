from github.ContentFile import ContentFile
import pkg_resources

from github import Github
from github import InputGitTreeElement

from loguru import logger
from jinja2 import Template


class GithubCredentials:
    """Basic class to store Github credentials and verify input"""

    def __init__(self, username=None, password=None, token=None):
        if not (username or password or token):
            raise ValueError("No credentials supplied")

        if username and password and token:
            raise ValueError("Can't pass in both username/password and token")

        if (username and not password) or (password and not username):
            raise ValueError("Username/password supplied but not the other")

        self.username = username
        self.password = password
        self.token = token


class GitRepo:
    """
    Extension of PyGithub with a couple of other helper methods.
    """

    def __init__(self, repo_name, credentials=None):
        """Retrieves a Repository by its fully qualified name. If credentials are passed
        they will be used."""
        if not credentials:
            self._github = Github().get_repo(repo_name)
        elif credentials.token:
            self._github = Github(credentials.token).get_repo(repo_name)
        else:
            self._github = Github(credentials.username, credentials.password).get_repo(
                repo_name
            )

    @property
    def github(self):
        """
        Direct access to the underlying PyGithub object.
        """
        return self._github

    def get_file(self, filename):
        """Fetch and decode the file from the master branch.
        Note that GitHub's API only supports files up to 1MB in size."""
        content_file = self._github.get_contents(filename)
        if isinstance(content_file, ContentFile):
            return content_file.decoded_content.decode("utf-8")
        else:
            raise ValueError("Did not get a single ContentFile (is this a directory?)")

    def modify_and_branch(
        self, base_branch, new_branch_name, commit_message, file_name, file_content
    ):
        """Create a new branch from base_branch, makes changes to a file, and
        commits it to the new branch."""

        base_sha = self._github.get_git_ref("heads/{}".format(base_branch)).object.sha
        base_tree = self._github.get_git_tree(base_sha)
        element = InputGitTreeElement(file_name, "100644", "blob", file_content)
        tree = self._github.create_git_tree([element], base_tree)

        parent = self._github.get_git_commit(base_sha)
        commit = self._github.create_git_commit(commit_message, tree, [parent])

        self._github.create_git_ref("refs/heads/{}".format(new_branch_name), commit.sha)

    def make_full_pr(
        self,
        base_branch: str,
        target_branch: str,
        software_name: str,
        software_current: str,
        software_latest: str,
        file_name: str,
        file_content: str,
        changelog_url: str,
        bot_info: dict,
        dry_run: bool = True,
    ):
        if target_branch in [x.name for x in list(self.github.get_branches())]:
            logger.info(f"branch already exists for {software_name}")
            return

        logger.info(
            f"updating {software_name} from {software_current} to {software_latest}"
        )
        if dry_run:
            return

        logger.info(f"creating new branch {target_branch}")
        self.modify_and_branch(
            base_branch,
            target_branch,
            f"automatically bump {software_name} to {software_latest}",
            file_name,
            file_content,
        )

        logger.info(f"making pull request for {software_name}")
        prtitle = f"[Automatic] Update {software_name} from {software_current} to {software_latest}."
        changelog_url = changelog_url.format(software_latest)

        template_file = pkg_resources.resource_filename(
            "adelie", "templates/version_bump_pr.jinja"
        )
        with open(template_file) as f:
            template = Template(f.read())
            prbody = template.render(
                changelog_url=changelog_url,
                bot_name=bot_info["name"],
                contact_info=bot_info["contact"],
            )

        self.github.create_pull(
            title=prtitle, body=prbody, head=target_branch, base=base_branch
        )
