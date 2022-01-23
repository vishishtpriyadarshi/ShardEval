# ShardEval - A Sharding based Blockchain Simulator

The simulator ShardEval is built on the top of [BlockEval](https://github.com/deepakgouda/BlockEval). More about the algorithm and simulator can be found [here](https://docs.google.com/document/d/1rB9lp8E5DQ6BXFdl3mfWjlItKq1i_78THTsPUrD1aXc/edit#).

## Setup
```bash
cd ShardEval
pip install -r requirements.txt
cd playground
```

## Usage 
```python
python simulate.py params/params.json > simulation_logs/simulation_results.log
```

Upon executing the simulator, a log file ```simulation_results.log``` containing the simulation results and entire lifecycle of the simulation will be generated.
