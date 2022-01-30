#!/usr/bin/env python

from distutils.core import setup

setup(name='HikeFlyScoring',
      version='1.0',
      description='Python Distribution Utilities',
      author='Ross Desmond',
      author_email='rdesmond91@gmail.com',
      packages=['parascoring/scoring', 'parascoring/scoring_lambda'],
      package_dir={'scoring': 'parascoring/scoring', 'scoring_lambda': 'parascoring/scoring_lambda'},
      requires=[
          'numpy',
          'configargparse',
          'boto3',
          'geopy'
        ])
