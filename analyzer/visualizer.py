import os
import sys
import pandas as pd
import matplotlib.pyplot as plt
import pathlib


# def __visualize(df, param_col, cond_col, plt_title, plt_name):
#     plt.figure()
    
#     num_nodes = df['Number of nodes'].unique()
#     cross_shard_tx_ratio = df['Fraction of cross-shard tx'].unique()
#     num_shards = df['Number of shards'].unique()
    
#     for n in sorted(num_nodes):
#         for ratio in sorted(cross_shard_tx_ratio):
#             rows = df.loc[(df['Number of nodes'] == n) & (df[cond_col] == ratio)]
#             rows = rows.sort_values(param_col)
#             x = rows[param_col]
#             y = rows['Processed TPS']
            
#             print(rows)

#             plt.xlabel(param_col)
#             plt.ylabel('Processed TPS')
#             plt.title(f'{plt_title} for n = {n}')
#             plt.plot(x, y, marker="o")
            
#         print(f"Saving plot for {plt_title} for n = {n}")
#         plt.legend(sorted(cross_shard_tx_ratio), loc='best', title=cond_col)
#         plt.grid(axis='y')
#         plt.savefig(f"{plt_name}_n{n}.png")
#         plt.show()
    

def visualize(filename, dir_name):
    df = pd.read_csv(filename)
    
    # plt_name = f"{dir_name}/{pathlib.PurePath(filename).with_suffix('').name}_shardsVsTPS"
    # __visualize(df, 'Number of shards', 'Fraction of cross-shard tx', 'No of shards vs TPS', plt_name)

    # plt_name = f"{dir_name}/{pathlib.PurePath(filename).with_suffix('').name}_txRatioVsTPS"
    # __visualize(df, 'Fraction of cross-shard tx', 'Number of shards', 'Fraction of cross-shard tx vs TPS', plt_name)
    
    num_nodes = df['Number of nodes'].unique()
    cross_shard_tx_ratio = df['Fraction of cross-shard tx'].unique()
    num_shards = df['Number of shards'].unique()
    
    for n in sorted(num_nodes):
        for ratio in sorted(cross_shard_tx_ratio):
            rows = df.loc[(df['Number of nodes'] == n) & (df['Fraction of cross-shard tx'] == ratio)]
            rows = rows.sort_values('Number of shards')
            x = rows['Number of shards']
            y = rows['Processed TPS']
            
            plt.xlabel('Number of shards')
            plt.ylabel('Processed TPS')
            plt.title(f'No of shards vs TPS for n = {n}')
            plt.plot(x, y, marker="o")
            
        print(f"Saving plot for shards vs TPS for n = {n}")
        plt.legend(sorted(cross_shard_tx_ratio), loc='best', title='Cross-shard tx ratio')
        plt.grid(axis='y')
        plt.savefig(f"{dir_name}/{pathlib.PurePath(filename).with_suffix('').name}_shardsVsTPS_n{n}.png")    
        plt.show()
    
    plt.figure()
    for n in sorted(num_nodes):
        for n_shard in sorted(num_shards):
            rows = df.loc[(df['Number of nodes'] == n) & (df['Number of shards'] == n_shard)]
            rows = rows.sort_values('Fraction of cross-shard tx')
            x = rows['Fraction of cross-shard tx']
            y = rows['Processed TPS']
            
            plt.xlabel('Fraction of cross-shard tx')
            plt.ylabel('Processed TPS')
            plt.title(f'Fraction of cross-shard tx vs TPS for n = {n}')
            plt.plot(x, y, marker="o")
            
        print(f"Saving plot for fraction of cross-shard tx vs TPS for n = {n}")
        plt.legend(sorted(num_shards), loc='best', title='Number of shards')
        plt.grid(axis='y')
        plt.savefig(f"{dir_name}/{pathlib.PurePath(filename).with_suffix('').name}_txRatioVsTPS_n{n}.png")    
        plt.show()
        

def main():
    filename = sys.argv[1]
    
    dir_name = f"logs_data/plots/{pathlib.PurePath(filename).parent.name}"
    if not os.path.exists(dir_name):
        print(f"Creating directory '{dir_name}' for storing plots\n")
    pathlib.Path(dir_name).mkdir(parents=True, exist_ok=True)

    visualize(filename, dir_name)
    

if __name__=="__main__":
    main()