import datetime
import os
import shutil
import tempfile

import datatig.exceptions
import datatig.process
import requests

import datatighubcore.git.repository
from datatighubcore.git.git import git_clone


class BaseCheckAndBuildIfNeededTask:

    def get_logging_message(self):
        raise Exception("Extending classes must implement!")

    def get_new_build(self):
        raise Exception("Extending classes must implement!")

    def get_git_url(self):

        raise Exception("Extending classes must implement!")

    def get_git_branch(self):
        raise Exception("Extending classes must implement!")

    def get_builds(self):
        raise Exception("Extending classes must implement!")

    def get_datatig_config_fallback_url(self):

        raise Exception("Extending classes must implement!")

    def get_save_dir(self):
        raise Exception("Extending classes must implement!")

    def build(self):
        # Start
        print("CheckAndBuildIfNeededTask for " + self.get_logging_message())
        build = self.get_new_build()
        tmp_directory = tempfile.mkdtemp(prefix="datatighub")

        # clone
        git_clone(
            self.get_git_url(),
            tmp_directory,
            "repository",
            branch=self.get_git_branch(),
            single_branch=True,
            depth=1,
        )
        git_repository = datatighubcore.git.repository.RepositoryAccessLocalGit(
            os.path.join(tmp_directory, "repository")
        )
        commit_hash = git_repository.get_current_commit()

        # What's the last commit we have?? Bail out if it's fine.
        builds = self.get_builds()
        latest_build = builds[0] if builds else None
        if latest_build and latest_build.commit == commit_hash:

            # Nothing to do!

            # clean up
            shutil.rmtree(tmp_directory)

        else:

            # Really start now
            build.started = datetime.datetime.now(tz=datetime.timezone.utc)
            build.save()

            try:

                # fallback config?
                if self.get_datatig_config_fallback_url():
                    if not (
                        os.path.exists(os.path.join(tmp_directory, "repository", "datatig.yaml"))
                        or os.path.exists(os.path.join(tmp_directory, "repository", "datatig.json"))
                    ):
                        response = requests.get(self.get_datatig_config_fallback_url())
                        # We assume YAML, not JSON.
                        # We could just document that somewhere, or check first character in file is a { or not.
                        with open(
                            os.path.join(tmp_directory, "repository", "datatig.yaml"),
                            "w",
                        ) as f:
                            f.write(response.text)

                # process
                datatig.process.go(
                    os.path.join(tmp_directory, "repository"),
                    sqlite_output=os.path.join(tmp_directory, "output.sqlite"),
                    frictionless_output=os.path.join(tmp_directory, "frictionless.zip"),
                )

                # make save dir
                os.makedirs(
                    os.path.join(
                        self.get_save_dir(),
                        "commit",
                        commit_hash,
                    ),
                    exist_ok=True,
                )

                # put output in storage
                shutil.copyfile(
                    os.path.join(tmp_directory, "output.sqlite"),
                    os.path.join(
                        self.get_save_dir(),
                        "commit",
                        commit_hash,
                        "output.sqlite",
                    ),
                )
                shutil.copyfile(
                    os.path.join(tmp_directory, "frictionless.zip"),
                    os.path.join(
                        self.get_save_dir(),
                        "commit",
                        commit_hash,
                        "frictionless.zip",
                    ),
                )

            except datatig.exceptions.SiteConfigurationException as exc:
                self._build.exception_site_configuration = str(exc)
                self._build.failed = datetime.datetime.now(tz=datetime.timezone.utc)
                self._build.save()
                shutil.rmtree(tmp_directory)
                return
            # except requests.exceptions.RequestException as e:
            except Exception as exc:
                self._build.exception = str(exc)
                self._build.failed = datetime.datetime.now(tz=datetime.timezone.utc)
                self._build.save()
                shutil.rmtree(tmp_directory)
                return

            # finished
            build.finished = datetime.datetime.now(tz=datetime.timezone.utc)
            build.commit = commit_hash
            build.save()

            # clean up
            shutil.rmtree(tmp_directory)
