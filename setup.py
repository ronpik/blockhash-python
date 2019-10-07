#!/usr/bin/env python

from distutils.core import setup

setup(
    name='imgblocks',
    version='0.1.1',
    description='Perceptual image hash calculation tool',
    author='Commons Machinery',
    author_email='dev@commonsmachinery.se',
    license='MIT',
    scripts=['blockhash/blockhash_cmd.py'],
    packages=['blockhash'],
    requires=['pillow'],
)
