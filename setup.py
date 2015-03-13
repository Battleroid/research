from setuptools import setup

setup(
    name='research',
    version='1.0.4',
    url='https://github.com/Battleroid/research',
    license='',
    author='Casey Weed',
    author_email='casweed@gmail.com',
    description='Used to split data sets and sort according to eigenvectors/eigenvalues and other thresholds.',
    packages=['research'],
    scripts=['bin/manager.py'],
    install_requires=['numpy', 'peewee', 'texttable']
)
