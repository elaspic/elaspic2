# ELASPIC2

[![conda](https://img.shields.io/conda/dn/ostrokach-forge/elaspic2.svg)](https://anaconda.org/ostrokach-forge/elaspic2/)
[![docs](https://img.shields.io/badge/docs-v0.1.2-blue.svg)](https://ostrokach.gitlab.io/elaspic-v2/v0.1.2/)
[![pipeline status](https://gitlab.com/ostrokach/elaspic-v2/badges/v0.1.2/pipeline.svg)](https://gitlab.com/ostrokach/elaspic-v2/commits/v0.1.2/)
[![coverage report](https://gitlab.com/ostrokach/elaspic-v2/badges/v0.1.2/coverage.svg)](https://ostrokach.gitlab.io/elaspic-v2/v0.1.2/htmlcov/)

Predicting the effect of mutations on protein folding and protein-protein interaction.

## Demo notebooks

The following notebooks can be used to explore the basic functionality of `proteinsolver`.

| Notebook name             | Google Colab                                                                                                                                                                          | Description                                                                                                    |
| ------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- |
| `10_stability_demo.ipynb` | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/elaspic/elaspic2/blob/master/notebooks/10_stability_demo.ipynb) | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein stability_.        |
| `10_affinity_demo.ipynb`  | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/elaspic/elaspic2/blob/master/notebooks/10_affinity_demo.ipynb)  | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein binding affinity_. |

See other notebooks in the [`notebooks/`]("notebooks/") directory for more detailed information about how ELASPIC2 models are trained and validated.

## Data

Data used to train and validate the ELASPIC2 models are available at <http://elaspic2.data.proteinsolver.org>.

See the [`protein-folding-energy`](https://gitlab.com/datapkg/protein-folding-energy) repository to see how these data were generated.
