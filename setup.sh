#!/bin/bash

function install() {
  local usecase=$1
  case "${usecase}" in
    localisation)
      git clone https://github.com/ci-group/revolve-localization.git localisation ;;
    mating)
      git clone https://github.com/ci-group/revolve-mating-server.git mating ;;    
    robot)
      git clone https://github.com/ci-group/revolve-brain.git brain
      git clone https://github.com/ci-group/revolve-communication.git com
      git clone https://github.com/ci-group/revolve-hal.git hal
      ;;
    sim)
      echo "Simulation not implemented currently." ;;
    *) echo "Unexpected option: ${usecase}" ; return 1 ;;
  esac
  return 0
}

function help() {
  echo "Help is underway!!!"
}

function main() {
  while [ $# -gt 0 ]; do
    option="$1"
    shift
    case "${option}" in
      --install) install $1 ; break ;;
      --help|-h) help ;;
      --) break ;;
      *) echo "Unexpected option: ${option}" ; exit 1 ;;
    esac
  done 
  exit 0
}

main $@
