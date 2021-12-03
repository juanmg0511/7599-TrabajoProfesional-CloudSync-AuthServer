import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "7599-TrabajoProfesional-CloudSync-AuthServer",
    version = "1.00",
    author = "Juan Manuel Gonzalez",
    author_email = "juanmg0511@gmail.com",
    description = "FIUBA - 7599",
    license = "GPLv3",
    keywords = "CloudSync AuthServer",
    url = "https://github.com/juanmg0511/7599-TrabajoProfesional-CloudSync-AuthServer",
    packages = ['','src','tests'], 
    install_requires=read('requirements.txt'),
    long_description=read('README.md'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Education",
        "License :: GPLv3 License",
    ],
)
