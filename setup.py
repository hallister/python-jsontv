from distutils.core import setup

setup(
    name='jsonTV',
    version='0.1.0',
    author='Justin Hall',
    author_email='jhall1468@gmail.com',
    packages=['jsontv'],
    url='http://pypi.python.org/pypi/jsonTV/',
    license='LICENSE.txt',
    description='A client for the Schedules Direct JSON API',
    long_description=open('README.txt').read(),
    install_requires=[
        "requires",
    ],
)
