from setuptools import setup
import os

setup(
    name="OSST DB",
    version="2.0.0",
    author="Olga Kopylova",
    description=("Database interaction package,"
                 "is necessary for osstnode and osstapi"),
    packages=['osstdb'],
    install_requires=['sqlalchemy', 'alembic']
)
