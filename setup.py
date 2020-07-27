from setuptools import setup, find_packages

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='cliffs',
    version='1.9',
    license='MIT',
    description='Command Line Interface Framework For Sane People',
    long_description=long_description,
    author='michalwa',
    author_email='michalwa2003@gmail.com',
    url='https://github.com/michalwa/py-cliffs',
    packages=find_packages(),
)
