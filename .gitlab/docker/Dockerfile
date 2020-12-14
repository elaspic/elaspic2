FROM nvidia/cuda:10.1-runtime-ubuntu18.04

ARG ENV_NAME=elaspic2
ARG ENV_VERSION=latest

RUN apt-get -qq -o=Dpkg::Use-Pty=0 update \
  && apt-get -y -qq -o=Dpkg::Use-Pty=0 install \
  curl \
  wget \
  ssh \
  && rm -rf /var/lib/apt/lists/*

SHELL ["/bin/bash", "-c"]

RUN groupadd -g 32766 lucky

RUN mkdir -p /opt/docker/bin /opt/conda \
  && curl -sS https://conda-envs.proteinsolver.org/${ENV_NAME}/${ENV_NAME}-${ENV_VERSION}.tar.gz | tar -xz -C /opt/conda/ \
  && . /opt/conda/bin/activate \
  && conda-unpack \
  && python -c "from elaspic2.plugins.protbert import ProtBert; ProtBert._download_model_data()" \
  && chgrp -R lucky /opt/conda \
  && chmod -R g=u /opt/conda

# Install additional conda packages
# RUN . /opt/conda/etc/profile.d/conda.sh \
#   && conda activate \
#   && conda install -yq -c conda-forge su-exec

# Give sudo permission for conda user to run yum (user creation is postponed
# to the entrypoint, so we can create a user with the same id as the host)
RUN echo 'conda ALL=NOPASSWD: /usr/local/bin/apt, /usr/bin/apt-get, /usr/bin/aptitude' >> /etc/sudoers

COPY entrypoint /opt/docker/bin/entrypoint

# Ensure that all containers start with tini and the user selected process.
# Activate the `conda` environment `base` and the devtoolset compiler.
# Provide a default command (`bash`), which will start if the user doesn't specify one.
ENTRYPOINT [ "/opt/conda/bin/tini", "--", "/opt/docker/bin/entrypoint" ]
CMD [ "/bin/bash" ]
