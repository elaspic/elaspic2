#!/usr/bin/env python
import re
from pathlib import Path

ROOT_DIR = Path(__file__).resolve(strict=True).parents[1]


def clean_text(text):
    text = text.replace(r"\n", "")
    text = text.replace("\\", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def clean_notebook_text(text):
    text = text.replace('    "    ', "")
    text = text.replace("!", "")
    text = text.replace('",', "")
    text = text.replace(r"\n", "")
    text = text.replace(r"\"", '"')
    text = text.replace("\\", "")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def command_to_colab(command):
    command = command.replace('"torch==1.8.1" ', "")
    return command


def get_match(text, command):
    idx = text.index("https://pytorch-geometric.com/whl/torch-1.8.0+cu101.html")
    match = text[idx - 15 : idx + len(command) - 15]
    return match


command = r"""
pip install -f https://pytorch-geometric.com/whl/torch-1.8.0+cu101.html --default-timeout=600 \
    "torch==1.8.1" \
    "transformers==3.3.1" \
    "torch-scatter==2.0.6" \
    "torch-sparse==0.6.9" \
    "torch-cluster==1.5.9" \
    "torch-spline-conv==1.2.1" \
    "torch-geometric==1.6.1" \
    "https://gitlab.com/kimlab/kmbio/-/archive/v2.1.0/kmbio-v2.1.0.zip" \
    "https://gitlab.com/kimlab/kmtools/-/archive/v0.2.8/kmtools-v0.2.8.zip" \
    "https://gitlab.com/ostrokach/proteinsolver/-/archive/v0.1.25/proteinsolver-v0.1.25.zip" \
    "git+https://gitlab.com/elaspic/elaspic2.git"
"""
command = clean_text(command)

with ROOT_DIR.joinpath("README.md").open("rt") as fin:
    readme_text = clean_text(fin.read())
assert command in readme_text, (command, get_match(readme_text, command))

with ROOT_DIR.joinpath("notebooks", "10_stability_demo.ipynb").open("rt") as fin:
    notebook_text = clean_notebook_text(fin.read())
assert command_to_colab(command) in notebook_text, (
    command_to_colab(command),
    get_match(notebook_text, command_to_colab(command)),
)

with ROOT_DIR.joinpath("notebooks", "10_affinity_demo.ipynb").open("rt") as fin:
    notebook_text = clean_notebook_text(fin.read())
assert command_to_colab(command) in notebook_text, (
    command_to_colab(command),
    get_match(notebook_text, command_to_colab(command)),
)

print(command)
