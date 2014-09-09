from distutils.core import setup

setup(
    name='python-gcmserver',
    version='0.0.1',
    packages=['samonitorserver'],
    license=open('LICENSE').read(),
    author="Gary O'Neall",
    author_email='gary@sourceauditor.com',
    url='https://github.com/goneall/SAHomeMonitor',
    description='Server code for the home alarm system',
    long_description=open('README.md').read(),
    keywords='android gcm raspberrypi alarm',
    tests_require = ['mock'],
)
