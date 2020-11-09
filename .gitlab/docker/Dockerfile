# FROM nvidia/cuda:10.1-runtime-ubuntu18.04
FROM ubuntu:20.04

ARG ENV_NAME=elaspic2
ARG ENV_VERSION=latest

RUN apt-get -qq update \
  && apt-get -y -qq install \
  curl \
  wget \
  ssh \
  && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /opt/conda/envs/${ENV_NAME} \
  && curl -sS https://conda-envs.proteinsolver.org/${ENV_NAME}/${ENV_NAME}-${ENV_VERSION}.tar.gz | tar -xz -C /opt/conda/envs/${ENV_NAME}
