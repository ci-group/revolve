#!/bin/bash

PROGNAME=$(basename $0)

function error_exit() {
  echo "${PROGNAME}: ${1:-"Unknown Error"}" 1>&2
  exit 1
}

function clone() {

  if [ $# -gt 0 ]; then
  local usecase="$1"
    shift
  else
    error_exit "${LINENO}: In ${FUNCNAME}() no usecase argument provided."
  fi

  case "${usecase}" in
    "localisation"|"loc")
      git clone https://github.com/ci-group/revolve-localization.git localisation ;;
    "mating"|"mat")
      git clone https://github.com/ci-group/revolve-mating-server.git mating ;;
    "server"|"srv")
      git clone https://github.com/ci-group/revolve-localization.git localisation
      git clone https://github.com/ci-group/revolve-mating-server.git mating
      ;;    
    "robot"|"rob")
      git clone https://github.com/ci-group/revolve-brain.git brain
      git clone https://github.com/ci-group/revolve-communication.git communication
      git clone https://github.com/ci-group/revolve-hal.git hal
      ;;
    "simulation"|"sim")
      echo "Simulation not implemented currently." ;;
    *) error_exit "${LINENO}: In ${FUNCNAME}() unexpected usecase option: ${usecase}" ;;
  esac
  return 0
}

function update() {

  find ./ -not -path '*/\.*' -type d -depth 1 -exec sh -c "git --git-dir={}/.git \
   --work-tree=$PWD/{} pull origin" \;
  return 0
}

function build() {

  local cwd=$(pwd)
  if [ $# -gt 0 ]; then
  local usecase="$1"
    shift
  else
    error_exit "${LINENO}: In ${FUNCNAME}() no usecase argument provided."
  fi

  case "${usecase}" in
    "localisation"|"loc")
      echo "Build of localisation not implemented currently" ;;
    "mating"|"mat")
      echo "Build of mating not implemented currently" ;;
    "server"|"srv")
      echo "Build of localisation and mating not implemented currently" ;; 
    "robot"|"rob")
      echo "Build of robot not implemented currently" ;;
    "simulation"|"sim")
      echo "Build of simulation not implemented currently" ;;
    *) error_exit "${LINENO}: In ${FUNCNAME}() unexpected usecase option: ${usecase}" ;;
  esac
  return 0
}

function help() {
  echo "Usage: ${PROGNAME} {clone|update|build|install|test} [usecase...]"
  echo "Actions:"
  echo "  clone        - clone designated usecase packages to project directory"
  echo "  update       - update usecase packages to latest version"
  echo "  build        - build libraries from usecase packages"
  echo "  install      - install executables from usecase packages"
  echo "  test         - run tests for usecase packages "
  echo "Usecases:"
  echo "  localisation (or loc)  - usecase for localisation module"
  echo "  mating (or mat)        - usecase for mating module"
  echo "  server (or srv)        - usecase for localisation and mating module"
  echo "  robot (or rob)         - usecase for robot module"
  echo "  simulation (or sim)    - usecase for simulation module"
  echo "Example: ${PROGNAME} clone mating"
}

function main() {

  if [ $# -gt 0 ]; then
    local acton="$1"
    shift
  else
    error_exit "${LINENO}: In ${FUNCNAME}() no argument provided."
  fi

  while [ $# -gt 0 ]; do
    local option="$1"
    shift
    case "${option}" in
      *) break ;;
    esac
  done

  case "${acton}" in
    "clone") clone ${option} ;;
    "update") update ;;
    "build") build ${option};;
    "install") ;;
    "test") ;;
    *) help ;;
  esac

  exit 0
}

main $@
