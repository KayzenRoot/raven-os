#!/usr/bin/env bash
# GitHub Actions standard-runner bootstrap for Raven M04 (Linux x86_64).
# Installs host tools, enforces disk policy, configures rootful Podman for osbuild.
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive
export PATH="/usr/local/bin:${HOME}/.local/bin:${PATH}"

# Minimum free bytes for Fedora/Kinoite layers + Raven OCI + image-builder + QCOW2 + osbuild temp.
MIN_FREE_BYTES=$((30 * 1024 * 1024 * 1024))
EVIDENCE_DIR=".build/evidence/github-actions"
mkdir -p "${EVIDENCE_DIR}"

log() {
  printf '%s\n' "$*" | tee -a "${EVIDENCE_DIR}/bootstrap.log"
}

free_bytes_root() {
  df -B1 --output=avail / | tail -n 1 | tr -d ' '
}

log_disk() {
  local label="$1"
  log "=== disk ${label} ==="
  df -h / | tee -a "${EVIDENCE_DIR}/bootstrap.log"
  log "FREE_BYTES_ROOT=$(free_bytes_root)"
}

if [[ "$(uname -s)" != "Linux" ]]; then
  log "error: GitHub Actions bootstrap requires Linux"
  exit 2
fi

arch="$(uname -m)"
if [[ "${arch}" != "x86_64" && "${arch}" != "amd64" ]]; then
  log "error: GitHub Actions bootstrap requires x86_64 (got ${arch})"
  exit 2
fi

log "RUNNER_OS=${RUNNER_OS:-unknown}"
log "RUNNER_ARCH=${RUNNER_ARCH:-unknown}"
log "kernel: $(uname -r)"
log_disk "before-packages"

if ! sudo -n true 2>/dev/null; then
  log "error: passwordless sudo is required on the GitHub runner"
  exit 2
fi
log "passwordless_sudo=ok"

maybe_cleanup_runner_caches() {
  local free_now
  free_now="$(free_bytes_root)"
  if [[ "${free_now}" -ge "${MIN_FREE_BYTES}" ]]; then
    log "disk_ok_before_cleanup free_bytes=${free_now} min=${MIN_FREE_BYTES}"
    return 0
  fi

  log "disk_low free_bytes=${free_now} min=${MIN_FREE_BYTES} — attempting safe cleanup"
  local categories=(
    "/usr/local/lib/android"
    "/usr/share/dotnet"
    "/opt/ghc"
    "/opt/hostedtoolcache/CodeQL"
    "/usr/local/share/boost"
    "/usr/share/swift"
    "/usr/local/share/chromium"
    "/usr/local/share/powershell"
    "/opt/microsoft"
    "/usr/local/julia*"
  )
  for path in "${categories[@]}"; do
    for match in ${path}; do
      if [[ -e "${match}" ]]; then
        log "removing ${match}"
        sudo rm -rf "${match}" || true
      fi
    done
  done
  sudo apt-get clean -y || true
  log_disk "after-cleanup"

  free_now="$(free_bytes_root)"
  if [[ "${free_now}" -lt "${MIN_FREE_BYTES}" ]]; then
    log "BLOCKED - STANDARD GITHUB RUNNER DISK CAPACITY"
    log "free_bytes=${free_now} required=${MIN_FREE_BYTES}"
    exit 2
  fi
}

maybe_cleanup_runner_caches

sudo apt-get update -y
sudo apt-get install -y \
  ca-certificates \
  curl \
  git \
  jq \
  ovmf \
  podman \
  python3 \
  qemu-system-x86 \
  qemu-utils \
  slirp4netns \
  uidmap
sudo apt-get install -y cpu-checker || true

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

log_disk "after-packages"
