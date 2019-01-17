from setuptools import setup, find_packages

setup(
    name='python-nhlapi',
    version='1',
    packages=find_packages(),
    install_requires=[i for i in open('requirements.txt', mode='r').readlines()],
    url='www.github.com/python-nhlapi',
    license='LGPL',
    author='Daniel Temkin',
    author_email='',
    description='Python Wrapper for (unofficial) NHL API'
)
