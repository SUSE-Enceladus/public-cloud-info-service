import os
import setuptools


HERE = os.path.dirname(__file__)
VERSION_FILE = os.path.join(HERE, 'VERSION.txt')

setuptools.setup(
    version_config={
        "count_commits_from_version_file": True,
        "dev_template": "{tag}.dev{ccount}",
        "dirty_template": "{tag}.dev{ccount}",
        "version_file": VERSION_FILE
    },
    setup_requires=['setuptools-git-versioning']
)
