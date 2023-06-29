from setuptools import setup, find_packages

setup(
    name='pylsat',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'fastapi', 
        'starlette', 
        'pymacaroons', 
        'datetime', 
        'hashlib', 
        'uuid',
        'bolt11 @ git+https://github.com/lnbits/bolt11.git',
    ],
    url='https://github.com/plebos/pylsat',
    license='MIT',
    author='Tal Shmueli',
    author_email='tal@shmueli.org',
    description='A Python library for validating Lightning Service Authentication Tokens (LSAT) in a FastAPI application.'
)
