import setuptools

with open("go2scope/dataio/README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="go2scope",
    version="1.0.0",
    author="Nenad Amodaj",
    author_email="nenad@go2scope.com",
    description="go2scope support functions for python: data I/O",
    long_description=long_description,
    packages=setuptools.find_packages(),
    install_requires=[
        'imageio==2.8.0', 'numpy==1.16.4', 'opencv-python==4.1.0.25', 'Pillow==7.1.1',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)