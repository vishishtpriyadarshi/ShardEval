<p align="center">
    <img src="https://github.com/vishishtpriyadarshi/ShardEval/blob/main/docs/ShardEval.png">
</p>


## Basic Overview
ShardEval is a **sharding-based blockchain simulator**. It is built on the top of [BlockEval](https://github.com/deepakgouda/BlockEval). More about the algorithm and simulator can be found here in this [doc](https://docs.google.com/document/d/1rB9lp8E5DQ6BXFdl3mfWjlItKq1i_78THTsPUrD1aXc/edit#).

![Architecture](docs/draft.png)

## Setup
```bash
cd ShardEval
pip install -r requirements.txt
bash setup.sh
```

## Usage 
The command-line interface for the doc-phi can be used as:

```
 __ _                   _   __            _ 
/ _\ |__   __ _ _ __ __| | /__\_   ____ _| |
\ \| '_ \ / _` | '__/ _` |/_\ \ \ / / _` | |
_\ \ | | | (_| | | | (_| //__  \ V / (_| | |
\__/_| |_|\__,_|_|  \__,_\__/   \_/ \__,_|_|

Usage: shard-eval [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  analyze-log           Analyze the generated log files
  batch-run-simulation  Initiate simulations in batches
  execute-simulator     execute simulator completely
  run-simulation        Initiate a simulation
  summarize-logs        Summarize the generated log files
  visualize-file        visualize the generated log files
```

A more elaborate explanation is as follows:

### 1. Running Simulation
The simulation can be executed by:
```
shard-eval run-simulation
```
The simulation executes as per the parameters specified in the
```config/params.json``` file. The result of the simulation are the log files which are stored accordingly in the folder ```simulation_logs```.

**Note:** To generate detailed logs, set ```verbose``` to 1 in the ```params.json``` file.

### 2. Running Simulation in Batch
The simulation can be executed in batch by using following command:
```
shard-eval batch-run-simulation
```

The ```script.py``` file needs to be changed accordingly to generate the logs as per the required parameters.

### 3. Analyzing the logs
The generated log files can be analyzed by:

```
shard-eval analyze-log <log_file>
```

Upon execution, several files (html, txt, csv, png) will be created in respective folders inside the ```logs_data``` which will contain a detailed analysis of the log file. 


### 4. Summarizing the logs (in batch)
To create a summary of the logs, following command can be used:

```
shard-eval summarize-logs <logs_directory>
```

A single csv file containing the summary of all the logs will be generated.


### 5. Visualizing the summary of the logs
After creating the summary, the csv file can be visualized using:

```
shard-eval visualize-file <summary_file>
```

Several plots will be created inside the suitable directories under the ```logs_data``` directory.


### 6. End-to-end execution of the simulator
To execute the simulator completely and perform all the steps in an instant, following command can be useful:

```
shard-eval execute-simulator
```

### Example log file

```
...
693.1657 : Node FN3 received a Final-block - B_FN11_31a7db44-ca47-4899-b078-82601fee8aeb from FN8
693.1657 : Node FN3 propagated Block B_FN11_31a7db44-ca47-4899-b078-82601fee8aeb to its neighbours ['FN8']
693.1665 : Node FN8 received a Final-block - B_FN11_31a7db44-ca47-4899-b078-82601fee8aeb from FN3
693.2447 : T_FN8_68c3437f-f6e3-4486-8d05-6ae26bf017f2 added to tx-pool of ['FN14']
...
719.8211 : T_FN12_a929b89a-3cf6-4707-af03-00b35500f8d4 added to tx-pool of ['FN10']
719.8211 : T_FN12_a929b89a-3cf6-4707-af03-00b35500f8d4 accepted by FN10
719.8226 : Node FN13 (Leader) received voted Cross-shard-block CB_FN10_0f76c779-d5f1-426d-b5c3-ca7adf928aa7 but it didn't originate in its own shard
719.8226 : Node FN13 propagated Voted-Cross-shard-block CB_FN10_0f76c779-d5f1-426d-b5c3-ca7adf928aa7 to its neighbours ['FN10']
719.8226 : Node FN13 received a Tx-block - TB_FN13_2077c41a-97a7-445f-be37-629ba6297036 from FN1
...

============  SIMULATION DETAILS  ============

Number of nodes = 15
Number of shards = 3
Fraction of cross-shard tx = 0.2
Simulation Time = 0.2716028690338135 seconds

Length of Blockchain = 8
Total no of transactions included in Blockchain = 132
Total no of intra-shard transactions included in Blockchain = 82
Total no of cross-shard transactions included in Blockchain = 50

Total no of transactions processed = 440
Total no of intra-shard transactions processed = 370
Total no of cross-shard transactions processed = 70

Total no of transactions generated = 525
Total no of intra-shard transactions generated = 412
Total no of cross-shard transactions generated = 113

Processed TPS = 0.22
Accepted TPS = 0.066
```