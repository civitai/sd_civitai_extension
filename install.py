import subprocess
import os
import sys

import git

import launch
from modules import shared

req_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")

def is_package_installed(package_name, version):
    # strip [] from package name
    package_name = package_name.split("[")[0]
    try:
        result = subprocess.run(['pip', 'show', package_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    except FileNotFoundError:
        return False
    if result.returncode == 0:
        for line in result.stdout.decode('utf-8').splitlines():
            if line.startswith('Version: '):
                installed_version = line.split(' ')[-1]
                if installed_version == version:
                    return True
    return False

civitai_skip_install = os.environ.get('CIVITAI_SKIP_INSTALL', False)

if not civitai_skip_install:
    with open(req_file) as file:
        for lib in file:
            lib = lib.strip()
            if not launch.is_installed(lib):
                launch.run_pip(f"install {lib}", f"Civitai Link requirement: {lib}")

if shared.opts.data.get('civitai_link_logging', True):
    base_dir = os.path.dirname(os.path.realpath(__file__))
    revision = ""
    app_revision = ""

    try:
        repo = git.Repo(base_dir)
        revision = repo.rev_parse("HEAD")
        app_repo = git.Repo(os.path.join(base_dir, "..", ".."))
        app_revision = app_repo.rev_parse("HEAD")
    except:
        pass
    print("")
    print("#######################################################################################################")
    print("Initializing Civitai Link")
    print("If submitting an issue on github, please provide the below text for debugging purposes:")
    print("")
    print(f"Python revision: {sys.version}")
    print(f"Civitai Link revision: {revision}")
    print(f"SD-WebUI revision: {app_revision}")
    print("")
    print("")
    print("#######################################################################################################")
