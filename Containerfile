# Raven OS V0.1 — bootc derivative image (M04 / INC-002)
# Base reference is controlled through build args; pin digest on the Builder via
# `just builder-preflight` and os/image-source.toml refresh.

ARG FEDORA_MAJOR=44
ARG BASE_IMAGE=quay.io/fedora/fedora-kinoite:44

FROM ${BASE_IMAGE}

LABEL org.opencontainers.image.title="Raven OS"
LABEL org.opencontainers.image.version="0.1.0-dev"
LABEL org.opencontainers.image.vendor="Raven OS Project"
LABEL io.raven.os.version="0.1"
LABEL io.raven.os.variant="vm-cognitive-seed"
LABEL io.raven.os.provenance="dev"
LABEL io.raven.os.fedora-major="${FEDORA_MAJOR}"

RUN mkdir -p /usr/lib/raven && \
    printf '%s\n' "Raven OS V0.1 VM Cognitive Seed" > /usr/lib/raven/release && \
    printf '%s\n' "0.1.0-dev" > /usr/lib/raven/version
