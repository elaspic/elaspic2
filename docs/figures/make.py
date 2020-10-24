#!/usr/bin/env python
import shlex
import shutil
import subprocess
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve(strict=True).parents[1]


def run_system_command(sc):
    proc = subprocess.run(
        shlex.split(sc),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        universal_newlines=True,
        cwd=PROJECT_ROOT,
    )
    if proc.stdout.strip():
        print(proc.stdout.strip())
    if proc.stderr.strip():
        print(proc.stderr.strip())
    if proc.returncode != 0:
        raise Exception(f"Process existed with non-zero return code: '{proc.returncode}'.")


def print_figures():
    files = [
        #
        "figure-1.html",
        "figure-2.html",
        "figure-s1.html",
    ]
    for file in files:
        file_path = Path(__file__).with_name(file).resolve(strict=True)
        sc = f"node ./scripts/export_pdf.js '{file_path}'"
        run_system_command(sc)

        sc = f"pdf2svg {file_path.with_suffix('.pdf')} {file_path.with_suffix('.svg')}"
        run_system_command(sc)

        for suffix in [".pdf", ".png", ".svg"]:
            output_file = file_path.with_suffix(suffix)
            output_file_2 = output_file.parent.joinpath("generated").joinpath(output_file.name)
            shutil.move(output_file, output_file_2)


if __name__ == "__main__":
    print_figures()
