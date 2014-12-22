import sys

if sys.version < '3.4':
    print('Sorry, this is not a compatible version of Python. Use 3.4 or later.')
    exit(1)

from setuptools import setup, find_packages

with open('README.md') as f:
    description = f.read()

from diana_ch import VERSION

setup(name='diana-ch',
      version=VERSION,
      description='Program for interacting with Artemis SBS with a CH Products Yoke',
      author='Alistair Lynn',
      author_email='arplynn@gmail.com',
      license="MIT",
      long_description=description,
      url='https://github.com/prophile/diana-ch',
      zip_safe=True,
      setup_requires=['nose >=1, <2'],
      install_requires=['libdiana >=0.0.6, <0.1'],
      entry_points={'console_scripts': [
          'dianach=diana_ch.cli:main'
      ]},
      packages=find_packages(),
      test_suite='nose.collector')

