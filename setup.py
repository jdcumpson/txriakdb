# -*- coding: utf-8 -*-
'''
Created on 2013-02-08

@author: Noobie
'''
try:
    from setuptools import setup, find_packages
except ImportError:
    from ez_setup import use_setuptools
    use_setuptools()
    from setuptools import setup, find_packages
    
from txriakdb import version

setup(
    name='txriakdb',
    version=version,
    description='Asynchronous python bindings for Riak databases',
    author='jdcumpson',
    author_email='cumpsonjd@gmail.com',
    zip_safe=False,
    url='https://github.com/jdcumpson/txriakdb',
    install_requires=[
        ],
    packages=find_packages(exclude=[]),
    include_package_data=True,
    entry_points={'console_scripts': []}
)

