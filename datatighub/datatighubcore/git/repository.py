import subprocess


# TODO DataTig library has a class we could maybe reuse here?
# https://github.com/DataTig/DataTig/blob/main/datatig/repository_access.py
class RepositoryAccessLocalGit:

    def __init__(self, directory):
        self._directory = directory

    def get_current_commit(self):
        process = subprocess.Popen(
            ["git", "rev-parse", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=self._directory,
        )
        stdout, stderr = process.communicate()
        return stdout.decode("utf-8").strip()
