import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import pathlib


def __visualize(df, base_list, param_list, cond_list, base_col, param_col, cond_col, tps_col, plt_title, plt_name):
    # plt.figure()
    
    for n in base_list:
        for m in cond_list:
            rows = df.loc[(df[base_col] == n) & (df[cond_col] == m)]
            rows = rows.sort_values(param_col)
            x = rows[param_col]
            y = rows[tps_col]
            
            plt.xlabel(param_col)
            plt.ylabel(tps_col)
            plt.title(f'{plt_title} for {base_col} = {n}')
            plt.plot(x, y, marker="o")

            plt.savefig(f"{plt_name}_{base_col}={n}_{cond_col}={m}.png")
            plt.figure()

            print(f"Saving plot for {plt_title} for {base_col} = {n} and {cond_col}={m}")
            
        plt.legend(cond_list, loc='best', title=cond_col)
        plt.grid(axis='y')
        # plt.savefig(f"{plt_name}_{base_col}={n}.png")
        # plt.show()
    

def visualize(filename, dir_name):
    df = pd.read_csv(filename)
    num_nodes = sorted(df['Number of nodes'].unique())
    cross_shard_tx_ratio = sorted(df['Fraction of cross-shard tx'].unique())
    num_shards = sorted(df['Number of shards'].unique())

    plt_name = f"{dir_name}/shardsVsTPS"
    __visualize(df, num_nodes, num_shards, cross_shard_tx_ratio, 'Number of nodes', 'Number of shards', \
            'Fraction of cross-shard tx', 'Processed TPS', 'No of shards vs TPS', plt_name)

    # plt_name = f"{dir_name}/{pathlib.PurePath(filename).with_suffix('').name}_txRatioVsTPS"
    # __visualize(df, num_nodes, cross_shard_tx_ratio, num_shards, 'Number of nodes', 'Fraction of cross-shard tx', \
    #         'Number of shards', 'Processed TPS', 'fraction of cross-shard tx vs TPS', plt_name)
        

def main():
    filename = sys.argv[1]
    
    parent_dir_name = f"logs_data/plots/{pathlib.PurePath(filename).parent.name}"
    exact_filename = pathlib.PurePath(filename).name
    dir_name = f"{parent_dir_name}/{exact_filename[:exact_filename.find('_')]}"
    
    if not os.path.exists(dir_name):
        print(f"Creating directory '{dir_name}' for storing plots\n")
    pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)
    
    visualize(filename, dir_name)
    

if __name__=="__main__":
    main()