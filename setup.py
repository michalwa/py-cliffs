from setuptools import setup

with open('README.md', 'r') as f:
    long_description = f.read()

setup(
    name='cliffs',
    version='1.4.7',
    license='MIT',
    description='Command Line Interface For Fucks Sake',
    long_description=long_description,
    author='michalwa',
    author_email='michalwa2003@gmail.com',
    url='https://github.com/michalwa/py-cliffs',
    packages=['cliffs']
)
