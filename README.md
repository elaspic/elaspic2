# ELASPIC2

[![conda](https://img.shields.io/conda/dn/ostrokach-forge/elaspic2.svg)](https://anaconda.org/ostrokach-forge/elaspic2/)
[![docs](https://img.shields.io/badge/docs-v0.1.2-blue.svg)](https://elaspic.gitlab.io/elaspic2/v0.1.2/)
[![pipeline status](https://gitlab.com/elaspic/elaspic2/badges/v0.1.2/pipeline.svg)](https://gitlab.com/elaspic/elaspic2/commits/v0.1.2/)
[![coverage report](https://gitlab.com/elaspic/elaspic2/badges/v0.1.2/coverage.svg)](https://elaspic.gitlab.io/elaspic2/v0.1.2/htmlcov/)

Predicting the effect of mutations on protein folding and protein-protein interaction.

## Usage

### Web server

ELASPIC2 has been integrated into the original ELASPIC web server: <http://elaspic.kimlab.org>.

### REST API

ELASPIC2 is accessible through a REST API, documented at: <https://elaspic.uc.r.appspot.com/docs>.

The following code snippet shows how the REST API can be accessed from within Python.

```python
import json
import time
import requests

ELASPIC2_JOBS_API = "https://elaspic.uc.r.appspot.com/jobs/"

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

### Demo notebooks

The following notebooks can be used to explore the basic functionality of `proteinsolver`.

| Notebook name             | Google Colab                                                                                                                                                                                               | Description                                                                                                    |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `10_stability_demo.ipynb` | <a href="https://colab.research.google.com/github/elaspic/elaspic2/blob/master/notebooks/10_stability_demo.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" width="200px" /></a> | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein stability_.        |
| `10_affinity_demo.ipynb`  | <a href="https://colab.research.google.com/github/elaspic/elaspic2/blob/master/notebooks/10_affinity_demo.ipynb"><img src="https://colab.research.google.com/assets/colab-badge.svg" width="200px" /></a>  | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein binding affinity_. |

See other notebooks in the [`notebooks/`](tree/master/notebooks/) directory for more detailed information about how ELASPIC2 models are trained and validated.

### Command-line interface (CLI)

ELASPIC2 can also be downloaded and used locally.

The easiest way to install ELASPIC2 is to use one of tarballs available at: <http://conda-envs.proteinsolver.org/elaspic2/>.

Simply download and extract the tarball into a desired directory and run `conda-unpack` to unpack.

```bash
wget http://conda-envs.proteinsolver.org/elaspic2/elaspic2-master.tar.gz
mkdir ~/elaspic2
tar -xzf elaspic2-master.tar.gz -C ~/elaspic2
source ~/elaspic2/bin/activate
conda-unpack
```

Alternatively, ELASPIC2 is also downloaded using `conda` or `pip`.

You can then use the ELASPIC2 CLI as follows:

```bash
python -m elaspic2 \
  --protein-structure tests/structures/1MFG.pdb \
  --protein-sequence GSMEIRVRVEKDPELGFSISGGVGGRGNPFRPDDDGIFVTRVQPEGPASKLLQPGDKIIQANGYSFINIEHGQAVSLLKTFQNTVELIIVREVSS \
  --ligand-sequence EYLGLDVPV \
  --mutations G1A.G1C
```

For examples of how to use the ELASPIC2 Python module, see the Google CoLab notebooks above.

## Data

Data used to train and validate the ELASPIC2 models are available at <http://elaspic2.data.proteinsolver.org> and <http://protein-folding-energy.data.proteinsolver.org>.

See the [`protein-folding-energy`](https://gitlab.com/datapkg/protein-folding-energy) repository to see how these data were generated.
