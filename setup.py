# -*- coding: utf_8 -*-
"""
"""

from setuptools import setup
from pypayline import VERSION


def load_requirements():
    """load requirements from requirements.txt"""
    with open('requirements.txt') as requirements_file:
        requirements = requirements_file.read().splitlines()
    # remove blank lines
    return filter(lambda line: bool(line), requirements)


setup(
    name='pypayline',
    version=VERSION,
    description="Python library for Payline",
    long_description='''
        Python interface for accessing the Payline payment service
        Based on SOAP API of Payline
    ''',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Communications',
        'Topic :: Software Development'
    ],
    keywords='payline, payment',
    author='Freexian',
    author_email='',
    maintainer='',
    maintainer_email='',
    url='',
    license='LGPL',
    packages=['pypayline', 'pypayline.backends'],
    platforms=["Linux", "Mac OS X", "Win"],
    install_requires=load_requirements(),
)
