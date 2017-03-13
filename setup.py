from setuptools import setup

setup(
    name="PySFCGAL",
    version="0.1",
    packages=["pysfcgal"],
    setup_requires=["cffi>=1.0.0"],
    cffi_modules=["pysfcgal/sfcgal_build.py:ffibuilder"],
    install_requires=["cffi>=1.0.0"],
)