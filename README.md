# ELASPIC2

[![conda](https://img.shields.io/conda/dn/ostrokach-forge/elaspic2.svg)](https://anaconda.org/ostrokach-forge/elaspic2/)
[![docs](https://img.shields.io/badge/docs-v0.1.0-blue.svg)](https://ostrokach.gitlab.io/elaspic-v2/v0.1.0/)
[![pipeline status](https://gitlab.com/ostrokach/elaspic-v2/badges/v0.1.0/pipeline.svg)](https://gitlab.com/ostrokach/elaspic-v2/commits/v0.1.0/)
[![coverage report](https://gitlab.com/ostrokach/elaspic-v2/badges/v0.1.0/coverage.svg)](https://ostrokach.gitlab.io/elaspic-v2/v0.1.0/htmlcov/)

Predicting the effect of mutations on protein folding and protein-protein interaction.

## Demo notebooks

The following notebooks can be used to explore the basic functionality of `proteinsolver`.

| Notebook name             | MyBinder                                                                                                                                                                                                                                      | Google Colab | Description                                                                                                    |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------ | -------------------------------------------------------------------------------------------------------------- |
| `10_stability_demo.ipynb` | [![binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/git/https%3A%2F%2Fmybinder%3AhTGKLsjmxRS8xNyHxRJB%40gitlab.com%2Fostrokach%2Fproteinsolver.git/v0.1.25?filepath=proteinsolver%2Fnotebooks%2F10_stability_demo.ipynb) |              | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein stability_.        |
| `10_affinity_demo.ipynb`  | [![binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/git/https%3A%2F%2Fmybinder%3AhTGKLsjmxRS8xNyHxRJB%40gitlab.com%2Fostrokach%2Fproteinsolver.git/v0.1.25?filepath=proteinsolver%2Fnotebooks%2F10_affinity_demo.ipynb)  |              | Example notebook showing how to use ELASPIC2 to predict the effect of mutations on _protein binding affinity_. |

See other notebooks in the [`notebooks/`]("notebooks/") directory for more detailed information about how ELASPIC2 models are trained and validated.

## Data

Data used to train and validate the ELASPIC2 models are available at <http://elaspic2.data.proteinsolver.org>.

See the [`protein-folding-energy`](https://gitlab.com/datapkg/protein-folding-energy) repository to see how these data were generated.
