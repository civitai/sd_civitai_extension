import subprocess
import os
import sys

import git

from launch import run

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
    # Loop through reqs and check if installed
    for req in reqs_dict:
        available = is_package_installed(req, reqs_dict[req])
        if available: print(f"[+] {req} version {reqs_dict[req]} installed.")
        else : print(f"[!] {req} version {reqs_dict[req]} NOT installed.")

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
