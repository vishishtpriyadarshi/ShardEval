#!/bin/bash

mkdir -p simulation_logs logs_data
mkdir -p logs_data/interactive_plots logs_data/metadata logs_data/plots logs_data/summary

chmod +x execute_simulator.sh
echo 'alias shard-eval="python3.8 $PWD/cli/shard_eval.py"' >> ~/.bash_aliases && source ~/.bash_aliases