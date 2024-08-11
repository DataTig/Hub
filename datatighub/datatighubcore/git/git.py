import subprocess


def git_clone(
    url,
    working_directory,
    target_directory,
    branch=None,
    single_branch=False,
    depth=None,
):
    command = ["git", "clone"]
    if branch:
        command += ["-b" + branch]
    if single_branch:
        command += ["--single-branch"]
    if depth:
        command += ["--depth=" + str(depth)]
    command += [url, target_directory]
    process = subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=working_directory,
    )
    stdout, stderr = process.communicate()
    if process.returncode:
        raise Exception(str(stderr))
