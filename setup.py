import setuptools

setuptools.setup(
    author="Allen Goodman",
    author_email="allen.goodman@icloud.com",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
    ],
    extras_require={
        "dev": [
            "sphinx>=3.1.2",
            "twine==3.1.1",
        ],
        "test": ["pytest~=7.4.1"],
        "wx": ["wxPython==4.1.0"],
    },
    install_requires=[
        "boto3>=1.12.28",
        "centrosome>=1.2.3,<1.3",
        "docutils==0.15.2",
        "h5py~=3.7.0",
        "matplotlib>=3.1.3",
        "numpy>=1.18.2",
        "prokaryote==2.4.4",
        "psutil>=5.7.0",
        "python-bioformats>=4.0.7,<5",
        "python-javabridge>=4.0.3,<5",
        "pyzmq~=22.3",
        "scikit-image==0.18.3",
        "scipy>=1.4.1",
    ],
    license="BSD",
    name="cellprofiler-core",
    package_data={"cellprofiler_core": ["py.typed"]},
    packages=setuptools.find_packages(exclude=["tests"]),
    python_requires=">=3.8",
    url="https://github.com/CellProfiler/core",
    version="4.2.8.1",
    zip_safe=False,
)
