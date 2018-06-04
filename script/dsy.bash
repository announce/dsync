#!/usr/bin/env bash

function dsy () {
  set -u

  init () {
    init-dependencies
  }

  init-dependencies () {
    local DEPENDENCIES=(
      "docker"
      "git"
    )
    for TARGET in "${DEPENDENCIES[@]}"; do
      if [[ ! -x "$(command -v "${TARGET}")" ]]; then
        error "Install ${TARGET}."
      fi
    done
  }

  lint () {
    lint-shell \
    && lint-python
  }

  lint-shell () {
    docker run --rm -v "$PWD:/mnt" koalaman/shellcheck:v0.5.0 \
      --exclude=SC1090 \
      script/*.bash
  }

  lint-python () {
    find . -type f -name "*.py" -print0 | xargs -0 \
    autopep8 --in-place --aggressive --aggressive \
    && flake8 .
  }

  run () {
    python dsync.py --help
  }

  clean () {
    docker system prune
  }

  error () {
    MESSAGE="${1:-Something went wrong.}"
    echo "[$(basename "$0")] ERROR: ${MESSAGE}" >&2
    exit 1
  }

  info () {
    MESSAGE="${1:-}"
    echo "[$(basename "$0")] INFO: ${MESSAGE}"
  }

  usage () {
    SELF="$(basename "$0")"
    echo -e "${SELF} -- elb-lint-docker
    \\nUsage: ${SELF} [arguments]
    \\nArguments:"
    declare -F | awk '{print "\t" $3}' | grep -v "${SELF}"
  }

  if [ $# = 0 ]; then
    usage
  elif [ "$(type -t "$1")" = "function" ]; then
    $1
  else
    usage
    error "Command not found."
  fi
}

dsy "$@"
