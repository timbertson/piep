#!/usr/bin/env python

## NOTE: ##
## this setup.py was generated by zero2pypi:
## http://gfxmonk.net/dist/0install/zero2pypi.xml

from setuptools import *
setup(
	packages = find_packages(exclude=['test', 'test.*']),
	entry_points={'console_scripts': ['piep=piep.command:main']},
	name='piep',
	url='http://gfxmonk.net/dist/0install/python-linewise.xml',
	py_modules=['codegen'],
	install_requires=['setuptools', 'python<3'],
	version='0.0.1',
	long_description='\n**Note**: This package has been built automatically by\n`zero2pypi <http://gfxmonk.net/dist/0install/zero2pypi.xml>`_.\nIf possible, you should use the zero-install feed instead:\nhttp://gfxmonk.net/dist/0install/python-linewise.xml\n\n----------------\n\n___\n',
	description="unix-style stream manipulation with python's syntax",
)
