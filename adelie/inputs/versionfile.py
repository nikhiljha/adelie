import copy
import tomlkit

from loguru import logger

from adelie.sources import make_source
from adelie.outputs.github_pr import GitRepo


def update(repo: GitRepo, name, file, config):
    current = file[name].get("version")
    file = copy.deepcopy(file)

    if current == None:
        logger.warning(f"unable to find current version for {name}")
        return

    helm = file[name].get("helm")
    if helm == None:
        logger.warning(f"versionfile only supports helm, skipping {name}")
        return

    backend = make_source("helm", file[name].get("chart", name))
    backend.refresh_source()
    latest = backend.get_latest()

    if latest != current:
        file[name]["version"] = latest
        content = tomlkit.dumps(file)
        repo.make_full_pr(
            latest, current, software, config, content
        )
    else:
        logger.info(f"{software['name']} is already {latest}, no need to update")
