FROM nvidia/cuda:10.1-runtime-ubuntu18.04

ARG ENV_NAME=elaspic2
ARG ENV_VERSION=latest

RUN apt-get -qq update \
  && apt-get -y -qq install \
  curl \
  wget \
  ssh \
  && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

RUN mkdir -p /opt/docker/bin /opt/conda \
  && curl -sS https://conda-envs.proteinsolver.org/${ENV_NAME}/${ENV_NAME}-${ENV_VERSION}.tar.gz | tar -xz -C /opt/conda/ \
  && . /opt/conda/bin/activate \
  && conda-unpack \
  && python -c "from elaspic2.plugins.protbert import ProtBert; ProtBert.load_model()" \
  && python -c "from elaspic2.plugins.proteinsolver import ProteinSolver; ProteinSolver.load_model()" \
  && chgrp -R lucky /opt/conda \
  && chmod -R g=u /opt/conda

COPY .gitlab/docker/entrypoint /opt/docker/bin/entrypoint

# Ensure that all containers start with tini and the user selected process.
# Activate the `conda` environment `base` and the devtoolset compiler.
# Provide a default command (`bash`), which will start if the user doesn't specify one.
ENTRYPOINT [ "/opt/conda/bin/tini", "--", "/opt/docker/bin/entrypoint" ]
CMD [ "/bin/bash" ]
