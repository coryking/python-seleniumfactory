from setuptools import setup, find_packages

setup(
    name='python-seleniumfactory',
    version='0.1',
    description="Python SeleniumFacotry",
    long_description="""
Simple interface factory to create Selenium objects, inspired by
SeleniumFactory interface from
https://github.com/infradna/selenium-client-factory.  The main objective is to
be able to have an automatic interface to easily run tests under the Bamboo
Sauce Ondemand plugin as well as local tests.  The factory object reads
environments variables setup by the Bamboo plugin and creates a remote Sauce
OnDemand session accordingly, otherwise it creates a local selenium
configuration.
    """,
    author='Matt Fair',
    author_email='matt.fair@gmail.com',
    maintainer='Erik LaBianca',
    maintainer_email='erik.labianca@wisertogether.com',
    url='https://github.com/WiserTogether/python-seleniumfactory',
    license='Unknown',
    platforms=['any'],
    packages=find_packages(),
    classifiers=[
        'Development Status :: 1 - Prerelease',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
