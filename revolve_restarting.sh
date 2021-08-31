#! /bin/bash

echo "Running command:"
echo "./revolve.py $@"
until ./revolve.py "$@"
do
    echo "Revolve crashed. This can be normal behaviour, because of third party software out of our control. Trying again in a few seconds.."
    sleep 2
done
