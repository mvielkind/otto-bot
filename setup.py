from setuptools import setup


with open('README.md') as readme_file:
    long_description = readme_file.read()


setup(
    name="otto-bot",
    version="0.0.2",
    packages=['otto'],
    install_requires=["twilio==6.26.1", "click==7"],
    python_requires='>=3.6',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url="https://github.com/mvielkind/otto-bot",
    entry_points={
        'console_scripts': [
            'otto-bot=otto.cli:handler'
        ]
    },
    author="Matthew Vielkind",
    author_email="matt@righthandcode.com",
    classifiers=[
        'Environment :: Console',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        "License :: OSI Approved :: MIT License",
    ]
)
