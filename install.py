import filecmp
import importlib.util
import os
import shutil
import sys
import sysconfig

import git

from launch import run

if sys.version_info < (3, 8):
    import importlib_metadata
else:
    import importlib.metadata as importlib_metadata

req_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "requirements.txt")


def check_versions():
    global req_file
    reqs = open(req_file, 'r')
    lines = reqs.readlines()
    reqs_dict = {}
    for line in lines:
        splits = line.split("==")
        if len(splits) == 2:
            key = splits[0]
            reqs_dict[key] = splits[1].replace("\n", "").strip()
    # print(f"Reqs dict: {reqs_dict}")
    checks = ["socketio[client]","blake3"]
    for check in checks:
        check_ver = "N/A"
        status = "[ ]"
        try:
            check_available = importlib.util.find_spec(check) is not None
            if check_available:
                check_ver = importlib_metadata.version(check)
                if check in reqs_dict:
                    req_version = reqs_dict[check]
                    if str(check_ver) == str(req_version):
                        status = "[+]"
                    else:
                        status = "[!]"
        except importlib_metadata.PackageNotFoundError:
            check_available = False
        if not check_available:
            status = "[!]"
            print(f"{status} {check} NOT installed.")
        else:
            print(f"{status} {check} version {check_ver} installed.")


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
civitai_skip_install = os.environ.get('CIVITAI_SKIP_INSTALL', False)

try:
    requirements_file = os.environ.get('REQS_FILE', "requirements_versions.txt")
    if requirements_file == req_file:
        civitai_skip_install = True
except:
    pass

if not civitai_skip_install:
    name = "Civitai Link"
    run(f'"{sys.executable}" -m pip install -r "{req_file}"', f"Checking {name} requirements...",
        f"Couldn't install {name} requirements.")

check_versions()
print("")
print("#######################################################################################################")
