#!/bin/bash

for i in exp*log; do echo -n "$i "; value=$(grep "Exported snapshot" $i|tail -n1|sed -E "s/\[(.*),.*Exported snapshot ([0-9]+).*/\2 -> \1/g"); echo $value; done
