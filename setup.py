#!/usr/bin/env python
from setuptools import *
setup(
	packages = find_packages(exclude=['test', 'test.*']),
	entry_points={'console_scripts': ['piep=piep.main:main']},
	name='piep',
	url='http://gfxmonk.net/dist/0install/piep.xml',
	install_requires=['python>=2.6', 'pygments'],
	version='0.8.1',
	description="unix-style stream manipulation with python's syntax",
)
