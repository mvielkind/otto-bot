from setuptools import setup


setup(
    name="otto-bot",
    version="0.0.1",
    packages=['otto'],
    entry_points={
        'console_scripts': [
            'otto-bot=otto.cli:handler'
        ]
    }
)
