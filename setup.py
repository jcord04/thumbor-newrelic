# coding: utf-8

from setuptools import setup, find_packages

setup(
    name='tc_newrelic',
    version="1.0.0",
    description='Thumbor metrics extension that forwards metrics to New Relic',
    long_description='''
Thumbor metrics extension that forwards metrics to New Relic.
This plugin collects metrics from Thumbor and forwards them to New Relic's Metric API.
''',
    author='Jez Cordonniner',
    author_email='',
    url='https://github.com/jcord04/thumbor-newrelic',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Topic :: Internet :: WWW/HTTP :: Dynamic Content',
        'Topic :: Multimedia :: Graphics :: Presentation'
    ],
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'thumbor>=7.0.0',
        'requests>=2.25.0'
    ],
    extras_require={
        'tests': [
            'pytest',
            'mock',
            'flake8',
            'coverage'
        ],
    }
)