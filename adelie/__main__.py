import click
import os
import tomllib

from loguru import logger

from adelie.outputs.github_pr import GitRepo
from adelie.outputs.github_pr import GithubCredentials

from adelie.inputs import regex
from adelie.inputs import versionfile

from adelie import __version__


@click.command()
@click.option("--config", default="config.toml", help="config file to use")
def main(config):
    """external dependency update tool for gitops"""
    logger.info(f"starting adelie v{__version__}")

    with open(config, "r") as file:
        config = tomllib.loads(file.read())
    if config == None or config == {}:
        raise Exception("Failed to read config file.")
    validate_config(config)

    gh_creds = os.environ["GITHUB_KEY"]
    assert len(gh_creds) == 40
    gh_creds = GithubCredentials(token=gh_creds)

    for repo in config["repo"]:
        git = GitRepo(repo["github_id"], gh_creds)

        # handle regex replaces
        for software in repo.get("regex", []):
            regex.update(git, software, config)

        # handle version files
        for filename in repo.get("versionfile", []):
            versions = tomllib.loads(repo.get_file(filename))
            for software in versions:
                versionfile.update(git, software, filename, config)

    logger.info("update check complete")


def validate_config(config: dict):
    assert len(config["settings"]["bot_name"]) > 1
    assert len(config["settings"]["contact_info"]) > 1


if __name__ == "__main__":
    main()
