# ELASPIC2

[![gitlab](https://img.shields.io/badge/GitLab-main-orange?logo=gitlab)](https://gitlab.com/elaspic/elaspic2)
[![docs](https://img.shields.io/badge/docs-v0.1.7-blue.svg?logo=gitbook)](https://elaspic.gitlab.io/elaspic2/v0.1.7/)
[![conda](https://img.shields.io/conda/dn/ostrokach-forge/elaspic2.svg?logo=conda-forge)](https://anaconda.org/ostrokach-forge/elaspic2/)
[![pipeline status](https://gitlab.com/elaspic/elaspic2/badges/v0.1.7/pipeline.svg)](https://gitlab.com/elaspic/elaspic2/commits/v0.1.7/)
[![coverage report](https://gitlab.com/elaspic/elaspic2/badges/v0.1.7/coverage.svg?job=docs)](https://elaspic.gitlab.io/elaspic2/v0.1.7/htmlcov/)

Predicting the effect of mutations on protein folding and protein-protein interaction.

## Usage

### Web server

`ELASPIC2` has been integrated into the original ELASPIC web server, available at: <http://elaspic.kimlab.org>.

### Python API

The following notebooks can be used to explore the basic functionality of `ELASPIC2`.

| Notebook name             | Google Colab                                                                                                                                                                                               | Description                                                                                                    |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `10_stability_demo.ipynb` | <a href="https://colab.research.google.com/github/elaspic/elaspic2/blob/master/notebooks/10_stability_demo.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" width="200px" /></a> | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein stability_.        |
| `10_affinity_demo.ipynb`  | <a href="https://colab.research.google.com/github/elaspic/elaspic2/blob/master/notebooks/10_affinity_demo.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" width="200px" /></a>  | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein binding affinity_. |

See other notebooks in the [`notebooks/`](https://gitlab.com/elaspic/elaspic2/-/tree/master/notebooks) directory for more detailed information about how ELASPIC2 models are trained and validated.

### REST API

`ELASPIC2` is accessible through a REST API, documented at: <https://elaspic2-api.proteinsolver.org/docs>.

The following code snippet shows how the REST API can be used from within Python.

```python
import json
import time
import requests

ELASPIC2_JOBS_API = "https://elaspic2-api.proteinsolver.org/jobs/"

mutation_info = {
    "protein_structure_url": "https://files.rcsb.org/download/1MFG.pdb",
    "protein_sequence": (
        "GSMEIRVRVEKDPELGFSISGGVGGRGNPFRPDDDGIFVTRVQPEGPASKLLQPGDKIIQANGYSFINI"
        "EHGQAVSLLKTFQNTVELIIVREVSS"
    ),
    "mutations": "G1A,G1C",
    "ligand_sequence": "EYLGLDVPV",
}

# Submit a job
job_request = requests.post(ELASPIC2_JOBS_API, json=mutation_info).json()
while True:
    # Wait for the job to finish
    time.sleep(10)
    job_status = requests.get(job_request["web_url"]).json()
    if job_status["status"] in ["error", "success"]:
        break
# Collect results
job_result = requests.get(job_status["web_url"]).json()
# Delete job (optional)
requests.delete(job_request["web_url"]).raise_for_status()
# Show results
print(job_result)
```

### Command-line interface (CLI)

Finally, `ELASPIC2` can be used through a command-line interface.

```bash
python -m elaspic2 \
  --protein-structure tests/structures/1MFG.pdb \
  --protein-sequence GSMEIRVRVEKDPELGFSISGGVGGRGNPFRPDDDGIFVTRVQPEGPASKLLQPGDKIIQANGYSFINIEHGQAVSLLKTFQNTVELIIVREVSS \
  --ligand-sequence EYLGLDVPV \
  --mutations G1A.G1C
```

## Installation

### Docker

Docker images that contain `ELASPIC2` and all dependencies are available at: <https://gitlab.com/elaspic/elaspic2/container_registry>.

### Conda-pack

Conda-pack tarballs containing `ELASPIC2` and all dependencies are available at: <http://conda-envs.proteinsolver.org/elaspic2/>.

Simply download and extract the tarball into a desired directory and run `conda-unpack` to unpack.

```bash
wget http://conda-envs.proteinsolver.org/elaspic2/elaspic2-latest.tar.gz
mkdir ~/elaspic2
tar -xzf elaspic2-latest.tar.gz -C ~/elaspic2
source ~/elaspic2/bin/activate
conda-unpack
```

### Conda

`ELASPIC2` can be installed using `conda`. However, the `torch-geometric` dependencies have to be installed separately.

Replace `cudatoolkit=10.1` and `cu101` with the desired CUDA version.

```bash
conda create -n elaspic2 -c pytorch -c ostrokach-forge -c conda-forge -c defaults elaspic2 "cudatoolkit=10.1"
conda activate elaspic2
pip install "torch-scatter==latest+cu101" -f https://pytorch-geometric.com/whl/torch-1.7.0.html
pip install "torch-sparse==latest+cu101" -f https://pytorch-geometric.com/whl/torch-1.7.0.html
pip install "torch-cluster==latest+cu101" -f https://pytorch-geometric.com/whl/torch-1.7.0.html
pip install "torch-spline-conv==latest+cu101" -f https://pytorch-geometric.com/whl/torch-1.7.0.html
pip install "torch-geometric==1.6.1"
```

### Python package index (PyPI)

`ELASPIC2` can be installed using `pip`. However, the `torch` and `torch-geometric` dependencies have to be installed from external channels.

Replace `cu101` with the desired CUDA version.

```bash
pip install -f https://pytorch-geometric.com/whl/torch-1.8.0+cu101.html --default-timeout=600 \
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
```

## Data

Data used to train and validate the `ELASPIC2` models are available at <http://elaspic2.data.proteinsolver.org> and <http://protein-folding-energy.data.proteinsolver.org>.

See the [`protein-folding-energy`](https://gitlab.com/datapkg/protein-folding-energy) repository to see how these data were generated.

## Acknowledgements

<div align="center">
<img src="docs/_static/acknowledgements.svg" width="45%" />
</div>

## References

- Alexey Strokach, Tian Yu Lu, Philip M. Kim. _ELASPIC2 (EL2): Combining contextualized language models and graph neural networks to predict effects of mutations_. Journal of Molecular Biology. <https://doi.org/10.1016/j.jmb.2021.166810>.
