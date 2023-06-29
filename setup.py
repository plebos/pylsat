from setuptools import setup, find_packages

setup(
    name='pylsat',
    version='0.2.6',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'starlette',
        'pymacaroons'
    ],
    url='https://github.com/plebos/pylsat',
    license='MIT',
    author='Tal Shmueli',
    author_email='tal@shmueli.org',
    description='A Python library for validating L402 (formerly known as LSAT) protocol for Lightning Network payments in a FastAPI application.'
)
