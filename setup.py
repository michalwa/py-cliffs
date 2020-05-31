from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='clifford',
    version='1.4.5',
    license='MIT',
    description='Command parser utility',
    long_description=long_description,
    author='michalwa',
    author_email='michalwa2003@gmail.com',
    url='https://github.com/michalwa/py-clifford',
    packages=['clifford']
)
