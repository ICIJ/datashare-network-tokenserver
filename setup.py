import sys
from tokenserver import __version__

from setuptools import setup, find_packages

py_version = sys.version_info[:2]
if py_version < (3, 7):
    raise Exception("datashare-network-tokenserver requires Python >= 3.7.")

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='datashare-network-tokenserver',
      version=__version__,
      packages=find_packages(),
      description="Datashare Network Token Server",
      use_pipfile=True,
      long_description=long_description,
      long_description_content_type="text/markdown",
      url="https://github.com/icij/datashare-network-tokenserver",
      tests_require=['pytest', 'responses'],
      setup_requires=['setuptools-pipfile'],
      keywords=['datashare', 'server', 'network', 'cryptography', 'authentication'],
      classifiers=[
          "Programming Language :: Python :: 3",
          "Programming Language :: Python :: 3.7",
          "Programming Language :: Python :: 3.8",
          "Programming Language :: Python :: 3.9",
          "Programming Language :: Python :: 3.10",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU Affero General Public License v3",
          "Operating System :: OS Independent",
          "Topic :: Security :: Cryptography"
      ],
      python_requires='>=3.7',
      )
