import os, sys
import json
import re
import csv
import glob


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
    filename = f"logs_data/summary/{os.path.basename(os.path.normpath(dir))}_summary.csv"
    
    writer = csv.writer(open(filename, 'w'))
    writer.writerow(col_names)

    for log_file in log_files:
        print(f"Summarizing {log_file} ...")
        row_data = []
        with open(log_file, 'r') as f:
            for line in f:
                for query in queries:
                    add_cell_entry(query, row_data, line)
            writer.writerow(row_data)

    print(f"\nWriting metadata in file '{filename}'\n")


def main():
    dir = sys.argv[1]
    summarize(dir)
    

if __name__=="__main__":
    main()