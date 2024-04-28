import re

from loguru import logger

from adelie.sources import make_source
from adelie.outputs.github_pr import GitRepo


def update(repo: GitRepo, software, config):
    regex = re.compile(software["regex"])
    content = repo.get_file(software["file"])
    current = next(iter(regex.findall(content)), None)

    if current == None:
        logger.warning(f"unable to find current version for {software['name']}")
        return

    backend = make_source(software["type"], software["id"], software.get("filter"))
    backend.refresh_source()
    latest = backend.get_latest()

    if latest != current:
        content = regex.sub(latest, content)
        repo.make_update_pr(
            latest, current, software, config, content
        )
    else:
        logger.info(f"{software['name']} is already {latest}, no need to update")
