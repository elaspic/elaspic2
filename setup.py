from setuptools import find_packages, setup


def read_file(file):
    with open(file) as fin:
        return fin.read()


def read_requirements():
    with open("requirements.txt") as fin:
        return [l.strip() for l in fin if l.strip()]


setup(
    name="elaspic2",
    version="0.1.7",
    description=(
        "Predicting the effect of mutations on protein folding and protein-protein interaction."
    ),
    long_description=read_file("README.md"),
    long_description_content_type="text/markdown",
    author="Alexey Strokach",
    author_email="alex.strokach@utoronto.ca",
    url="https://gitlab.com/elaspic/elaspic2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    package_data={
        "elaspic2": [
            "data/pca/*",
            "data/lgb/*",
            "plugins/proteinsolver/data/ps_191f05de/e53-s1952148-d93703104.state",
            "plugins/protbert/data/prot_bert_bfd/config.json",
            "plugins/protbert/data/prot_bert_bfd/vocab.txt",
        ]
    },
    install_requires=read_requirements(),
    include_package_data=True,
    zip_safe=False,
    keywords="elaspic2",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
    ],
    test_suite="tests",
)
