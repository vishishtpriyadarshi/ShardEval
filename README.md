# ShardEval - A Sharding based Blockchain Simulator

The simulator ShardEval is built on the top of [BlockEval](https://github.com/deepakgouda/BlockEval). More about the algorithm and simulator can be found here in this [doc](https://docs.google.com/document/d/1rB9lp8E5DQ6BXFdl3mfWjlItKq1i_78THTsPUrD1aXc/edit#).

![Architecture](docs/draft.png)

## Setup
```bash
cd ShardEval
pip install -r requirements.txt
```

## Usage 

### Execution of the Simulator
The simulator can be executed in 2 ways -
1. Using ```simulate.py``` to generate a single log file

    ```bash
    mkdir simulation_logs
    python simulate.py
    ```

2. Using ```script.py``` to generate log files in bulk

    ```bash
    mkdir simulation_logs
    python script.py
    ```

    The script files need to be modified suitably to generate logs with suitable parameters. The parameters can be modified fron the ```config/params.json``` file.

**Note:** To generate detailed logs, set ```verbose``` to 1 in the ```params.json``` file.


### Output from the Simulator
Upon executing the simulator, log file(s) containing the simulation results and entire lifecycle of the simulation will be generated.  
In case of ```simulate.py```, the log file will be named as ```simulation_results.log```, while in case of ```script.py```, more elaborate naming convention is followed and logs fils are stored in a directory structure representing current dare and time.


### Analysis of the Logs
To analyse the generated log file -
```bash
mkdir logs_data/interactive_plots logs_data/metadata logs_data/plots logs_data/summary
python analyzer/log_analyzer.py <log_file>
```

To generate the summary of the generated log files present in a directory -
```bash
mkdir logs_data/summary
python analyzer/log_summarizer.py <directory_name>
```

Upon execution, several files (html, txt, csv, png) will be created in respective folders inside the ```logs_data```.   