from setuptools import setup

setup(
    name='jsonTV',
    version='0.1.0',
    author='Justin Hall',
    author_email='jhall1468@gmail.com',
    py_modules=['jsontv'],
    url='http://pypi.python.org/pypi/jsonTV/',
    license='APACHE 2.0',
    description='A client for the Schedules Direct JSON API',
    long_description=open('README.rst').read(),
    install_requires=[
        "requests",
    ],
)
