import os, sys, inspect
import json
import re
import csv
import glob
import pathlib

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
from utils.color_print import ColorPrint


def add_cell_entry(query, row_data, line):
    res = re.search(query, line)
    if res:
        row_data.append(line[res.end() : len(line)-1])


def summarize(dir):
    log_files = glob.glob(dir+'/*')
    queries = ['Number of nodes = ', 'Number of shards = ', 'Fraction of cross-shard tx = ', 'Total no of transactions included in Blockchain = ', \
                'Total no of intra-shard transactions included in Blockchain = ', 'Total no of cross-shard transactions included in Blockchain = ', \
                'Total no of transactions processed = ', 'Total no of intra-shard transactions processed = ', 'Total no of cross-shard transactions processed = ', \
                'Total no of transactions generated = ', 'Total no of intra-shard transactions generated = ', 'Total no of cross-shard transactions generated = ', \
                'Processed TPS = ', 'Accepted TPS = ']
    
    col_names = [name.rstrip(' = ') for name in queries]
    
    dir_name = f"logs_data/summary/{pathlib.PurePath(dir).parent.name}"
    if not os.path.exists(dir_name):
        ColorPrint.print_info(f"\n[Info]: Creating directory '{dir_name}' for storing summary of the simulation logs\n")
    pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)

    filename = f"{dir_name}/{os.path.basename(os.path.normpath(dir))}_summary.csv"
    writer = csv.writer(open(filename, 'w'))
    writer.writerow(col_names)

    for log_file in log_files:
        ColorPrint.print_info(f"[Info]: Summarizing {log_file} ...")
        row_data = []
        with open(log_file, 'r') as f:
            for line in f:
                for query in queries:
                    add_cell_entry(query, row_data, line)
            writer.writerow(row_data)

    ColorPrint.print_info(f"[Info]: Writing metadata in file '{filename}'\n")


def main():
    if len(sys.argv) == 1:
        ColorPrint.print_fail(f"\n[Error]: log file not specified")
        exit(1)

    dir = sys.argv[1]
    summarize(dir)
    

if __name__=="__main__":
    main()