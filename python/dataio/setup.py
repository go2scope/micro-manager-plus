import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dataio",
    version="0.0.0",
    author="Nenad Amodaj",
    author_email="nenad@go2scope.com",
    description="Data IO package for Micro Manager image format.",
    long_description=long_description,
    packages=setuptools.find_packages(),
    install_requires=[
        'opencv-python==4.1.0.25',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)