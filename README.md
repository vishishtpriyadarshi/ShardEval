# ShardEval - A Sharding based Blockchain Simulator

The simulator ShardEval is built on the top of [BlockEval](https://github.com/deepakgouda/BlockEval). More about the algorithm and simulator can be found [here](https://docs.google.com/document/d/1rB9lp8E5DQ6BXFdl3mfWjlItKq1i_78THTsPUrD1aXc/edit#).

![Architecture](docs/draft.png)

## Setup
```bash
cd ShardEval
pip install -r requirements.txt
```

## Usage 

### 1. ShardEval
```python
mkdir simulation_logs
python simulate.py
```
Upon executing the simulator, a log file ```simulation_results.log``` containing the simulation results and entire lifecycle of the simulation will be generated.
 
To analyse the generated log file -
```python
mkdir logs_data/interactive_plots logs_data/metadata logs_data/plots
python analyzer/log_analyzer.py <log_file>
```

Upon execution, several files (html, txt, csv, png) will be created in respective folders inside the ```logs_data```.   


**Note:**   
Create log files in batch by modifying the ```script.py``` file and executing it using ```python script.py```

### 2. BlockEval (*Playground*)
```python
cd playground
python simulate.py params/params.json > simulation_logs/simulation_results.log
```



### Steps
###### Execution of simulate.py
1. Params are loaded from config/params.json - file read
2. Simpy environment is initialized
3. execute_simulation method is invoked

###### Execution of execute_simulation
1. Network object is initialized with the given params and env
    1.1 Iterates over the number of nodes and initializes the participating nodes dictionary
2. Sybil resistance mechanism executed for all the participating nodes - a method of network class
    2.1 Generates a binary mask of length num nodes - dummy step as of now
    2.2 Based on bits which are on, the participating nodes are converted to full nodes
3. run_epoch method is invoked, Epochs are executed - frequency is taken from params file

###### run_epoch method
1. partition_nodes method is invoked
    1.1 Prinipal committee is formed
    1.2 Prinipal committee leader is selected - randomly
    1.3 Each Principal committee node is given node is 1 and leader id is stored
    1.4 Shard nodes are defined - rest all nodes
    1.5 Shard leader is selected randomly and assigned and is of 2

2. 
