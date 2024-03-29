#!/usr/bin/env python3
from setuptools import *
setup(
	packages = find_packages(exclude=['test', 'test.*']),
	entry_points={'console_scripts': ['piep=piep.main:main']},
	name='piep',
	url='http://gfxmonk.net/dist/0install/piep.xml',
	install_requires=['pygments'],
	version='0.10.0',
	description="unix-style stream manipulation with python's syntax",
	test_suite = 'nose.collector',
	tests_require = ['nose'],
)
