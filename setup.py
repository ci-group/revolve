#!/usr/bin/env python
from distutils.core import setup

setup(name='revolve',
      version=0.2,
      description='Revolve: robot evolution framework',
      author='Elte Hupkes',
      author_email='elte@hupkes.org',
      url='https://github.com/ElteHupkes/revolve',
      packages=['revolve', 'revolve.gazebo', 'revolve.build', 'revolve.build.sdf',
                'revolve.convert', 'revolve.generate', 'revolve.spec', 'revolve.angle',
                'revolve.util'],
      install_requires=['PyYAML', 'pygazebo', 'protobuf', 'sdfbuilder', 'numpy', 'psutil']
      )
