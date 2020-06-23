from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='cliffs',
    version='1.6.3',
    license='MIT',
    description='Command Line Interface Framework For Sane People',
    long_description=long_description,
    author='michalwa',
    author_email='michalwa2003@gmail.com',
    url='https://github.com/michalwa/py-cliffs',
    packages=['cliffs']
)
