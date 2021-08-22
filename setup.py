import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mercadoBTCUtils", # Replace with your own username
    version="1.0.0_rc1",
    author="Mateus Interciso",
    author_email="minterciso@gmail.com",
    description="A suite of tools to control the Mercado Bitcoin APIs. Also some very simple ML analysis.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/minterciso/mercadoBTCUtils",
    packages=setuptools.find_packages(),
    install_requires=[
        'pandas>=1.3.2',
        'scikit-learn>=0.24.2',
        'seaborn>=0.11.2',
        'matplotlib>=3.4.3',
        'numpy>=1.21.2',
        'urllib3>=1.26.6',
        'requests>=2.26.0'
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
