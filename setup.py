#!/usr/bin/env python3
from __future__ import absolute_import

from setuptools import setup

setup(name='pyrevolve',
      version='0.3',
      description='Revolve: robot evolution framework',
      author='CI Group',
      author_email='m.decarlo@vu.nl',
      url='https://github.com/ci-group/revolve',
      packages=[
          'pyrevolve',
          'pyrevolve.angle',
          'pyrevolve.build',
          'pyrevolve.build.sdf',
          'pyrevolve.convert',
          'pyrevolve.gazebo',
          'pyrevolve.generate',
          'pyrevolve.spec',
          'pyrevolve.sdfbuilder',
          'pyrevolve.util',
      ],
      install_requires=[
          'numpy',
          'protobuf',
          'pygazebo',
          'PyYAML',
          'psutil',
      ])
