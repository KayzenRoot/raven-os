#!/usr/bin/env bash
# Cirrus Community Cluster bootstrap for Raven M04 (Linux x86_64 full VM).
# Installs host tools only. Image/QCOW2 work stays in Justfile/scripts.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export PATH="/usr/local/bin:${HOME}/.local/bin:${PATH}"

log() {
  printf '%s\n' "$*"
}

if [[ "$(uname -s)" != "Linux" ]]; then
  log "error: cirrus bootstrap requires Linux"
  exit 2
fi

arch="$(uname -m)"
if [[ "${arch}" != "x86_64" && "${arch}" != "amd64" ]]; then
  log "error: cirrus bootstrap requires x86_64 (got ${arch})"
  exit 2
fi

if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update -y
  sudo apt-get install -y \
    ca-certificates \
    curl \
    git \
    ovmf \
    podman \
    python3 \
    qemu-system-x86 \
    qemu-utils \
    slirp4netns \
    uidmap
  sudo apt-get install -y cpu-checker || true
elif command -v dnf >/dev/null 2>&1; then
  sudo dnf install -y \
    curl \
    git \
    podman \
    python3 \
    qemu-kvm \
    qemu-img \
    edk2-ovmf \
    slirp4netns
else
  log "error: neither apt-get nor dnf is available"
  exit 2
fi

if [[ -e /dev/kvm ]]; then
  sudo chmod a+rw /dev/kvm || true
  log "KVM_PRESENT=1"
else
  log "KVM_PRESENT=0 (QEMU TCG remains allowed on cloud)"
fi

if ! command -v uv >/dev/null 2>&1; then
  curl -LsSf https://astral.sh/uv/install.sh | sudo env UV_INSTALL_DIR=/usr/local/bin sh
fi

if ! command -v just >/dev/null 2>&1; then
  curl --proto '=https' --tlsv1.2 -sSf https://just.systems/install.sh \
    | sudo bash -s -- --to /usr/local/bin
fi

log "podman: $(command -v podman)"
podman --version || true
log "qemu: $(command -v qemu-system-x86_64)"
qemu-system-x86_64 --version | head -n 1 || true
log "uv: $(command -v uv)"
uv --version
log "just: $(command -v just)"
just --version
log "RAVEN_CLOUD_BUILDER=${RAVEN_CLOUD_BUILDER:-}"

uv python install 3.12
uv sync --extra dev --python 3.12
