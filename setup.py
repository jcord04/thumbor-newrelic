# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='tc_newrelic',
    version="0.0.1",
    description='Thumbor NewRlic extension',
    author='Jez Cordonniner,
    author_email='',
    zip_safe=False,
    include_package_data=True,
    packages=find_packages(),
    install_requires=[
        'thumbor',
        'newrelic-metrics',
    ]
)
