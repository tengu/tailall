from setuptools import setup
    
setup(
    name="tailall",
    version="0.0.1",
    entry_points="""
    [console_scripts]
    tailall = tailall:main
    """,
    py_modules=['tailall'],
    license = "LGPL",
    description = "tail every file under a directory",
    long_description="""tailall uses inotify to discover files that are getting written to and tails them all to create a merged log stream.""",
    author = "tengu",
    author_email = "karasuyamatengu@gmail.com",
    # url = "https://github.com/tengu/tailall",
    classifiers = [ # see http://pypi.python.org/pypi?%3Aaction=list_classifiers
        "License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)",
        "Environment :: Console",
        "Programming Language :: Python",
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities", 
        ],
    install_requires='pyinotify'.split(),
)
