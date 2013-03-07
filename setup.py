#!/usr/bin/env pythonv

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup

import sys
Version = "0.3"

if float("%d.%d" % sys.version_info[:2]) < 2.6:
    sys.stderr.write("Your Python version %d.%d.%d is not supported.\n" % sys.version_info[:3])
    sys.stderr.write("eeagent requires Python 2.6 or newer.\n")
    sys.exit(1)

setup(name='pyhantom',
      version=Version,
      description='AWS Autoscale clone-ish',
      author='Nimbus Development Team',
      author_email='workspace-user@globus.org',
      url='http://www.nimbusproject.org/',
      packages=find_packages(),
      keywords = "Nimbus auto scale",
      long_description="""Some other time""",
      license="Apache2",
      install_requires = ["simplejson == 2.3.2", "boto >= 2.6", "dashi", "ceiclient", "sqlalchemy == 0.7.6", "wsgiref", "webob", "cherrypy >= 3.2", "mysql-python == 1.2.3"],
      entry_points = {
        'console_scripts': [
            'phantomwsgiref = pyhantom.execs.simpleref:main',
            'phantomcherrypy = pyhantom.execs.cherrypy_exe:main',
            'phantomparse = pyhantom.execs.parse_launch_plan:main',
            'phantomclient = pyhantom.execs.client:main'

        ],},

      classifiers=[
          'Development Status :: 4 - Beta',
          'Environment :: Console',
          'Intended Audience :: End Users/Desktop',
          'Intended Audience :: Developers',
          'Intended Audience :: System Administrators',
          'License :: OSI Approved :: Apache Software License',
          'Operating System :: MacOS :: MacOS X',
          'Operating System :: Microsoft :: Windows',
          'Operating System :: POSIX',
          'Operating System :: POSIX :: Linux',
          'Programming Language :: Python',
          'Topic :: System :: Clustering',
          'Topic :: System :: Distributed Computing',
          ],
     )
