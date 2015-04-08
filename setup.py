#!/usr/bin/env python
from distutils.core import setup

setup(name='ToL Robogen Specification',
      version=0.1,
      description='ToL Robogen Protobuf spec',
      author='Elte Hupkes',
      author_email='elte@hupkes.org',
      url='https://github.com/ElteHupkes/tolrg-spec',
      packages=['tolrgspec'],
      package_dir={'tolrgspec': 'src/python'}
      )
