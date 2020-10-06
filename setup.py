from setuptools import find_packages, setup


def read_md(file):
    with open(file) as fin:
        return fin.read()


setup(
    name="ev2",
    version="0.1.0",
    description=(
        "Predicting the effect of mutations on protein folding and protein-protein interaction."
    ),
    long_description=read_md("README.md"),
    author="Alexey Strokach",
    author_email="alex.strokach@utoronto.ca",
    url="https://gitlab.com/ostrokach/elaspic-v2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={},
    include_package_data=True,
    zip_safe=False,
    keywords="elaspic_v2",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
)
