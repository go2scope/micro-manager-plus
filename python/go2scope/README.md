Copyright (c) 2019 The Python Packaging Authority
# **go2Scope** Python Package
[go2Scope](https://go2scope.com) is a microscopy automation programming environment, based on the popular Open Source microscopy software [micro-manager](https://micro-manager.org). **go2Scope** mainly solves issues with controlling multiple microscopes in a highly automated distributed environment.

Python package is intended to provide utilities for interfacing to **go2scope** which is mainly written in C++ and Java.

## **dataio** sub-package ##
Reading and writing of "classic" micromanager datasets. Classic dataset is a folder with sub-folders containing metadata and individual image files. Each image can be accessed with four integer coordinates: position, channel, slice and time-point.

This package does not work with OME compatible "image stack files".