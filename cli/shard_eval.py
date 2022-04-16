import click, time
from pyfiglet import Figlet
from halo import Halo
import signal, pickle
import os, sys, subprocess


def pass_handler(signal, frame):
    pass


def execute_command(filename, parameter):
    cmd = ['python', filename]
    if parameter:
        cmd.append(parameter)
    
    proc = subprocess.Popen(cmd)
    proc.wait()

    (stdout, stderr) = proc.communicate()
    if proc.returncode != 0:
        sys.exit("\x1b[1;31m[script.py]: Aw, Snap! An error has occurred")
    

@click.group()
def main():
    f = Figlet(font='ogre')
    click.secho(f.renderText('ShardEval'), fg='green')
    

@main.command(help='Initiate a simulation')
def run_simulation():
    spinner = Halo(text='Running simulation', text_color='yellow', spinner='dots')
    
    spinner.start()
    execute_command('simulate.py', None)
    spinner.stop()

    click.secho('[✓]: Simulation completed', fg='green')
    

@main.command(help='Initiate simulations in batches')
def batch_run_simulation():
    spinner = Halo(text='Running simulations in batches', text_color='yellow', spinner='dots')
    
    spinner.start()
    spinner.stop_and_persist(symbol='⌛'.encode('utf-8'), text='Running simulations in batches')
    execute_command('script.py', None)
    
    click.secho('\n[✓]: Simulations completed', fg='green')


@main.command(help='Analyze the generated log files')
@click.option('--log_file', help='log file')
def analyze_log(log_file):
    spinner = Halo(text='Analyzing simulation log', text_color='yellow', spinner='dots')
    
    spinner.start()
    spinner.stop_and_persist(symbol='⌛'.encode('utf-8'), text='Analyzing simulation logs')

    execute_command('analyzer/log_analyzer.py', log_file)
    spinner.text_color = 'green'
    spinner.succeed('Analyzed the log file')


@main.command(help='Summarize the generated log files')
@click.option('--log_dir', help='logs directory')
def summarize_logs(log_dir):
    spinner = Halo(text='Summarizing simulation logs', text_color='yellow', spinner='dots')
    
    spinner.start()
    spinner.stop_and_persist(symbol='⌛'.encode('utf-8'), text='Summarizing simulation logs')
    execute_command('analyzer/log_summarizer.py', log_dir)
    spinner.text_color = 'green'
    spinner.succeed('Summarized the logs')


@main.command(help='visualize the generated log files')
@click.option('--summary_file', help='log file')
def visualize_file(summary_file):
    spinner = Halo(text='Visualizing the summary file', text_color='yellow', spinner='dots')
    
    spinner.start()
    spinner.stop_and_persist(symbol='⌛'.encode('utf-8'), text='Visualizing the summary file')
    execute_command('analyzer/visualizer.py', summary_file)
    spinner.text_color = 'green'
    spinner.succeed('Visualized the summary file')


@main.command(help='execute simulator completely')
def execute_simulator():
    spinner = Halo(text='Visualising summary files', text_color='yellow', spinner='dots')
    
    spinner.start()
    spinner.stop_and_persist(symbol='⌛'.encode('utf-8'), text='Executing simulator')
    subprocess.call("execute_simulator.sh")

    click.secho('[✓]: Completed end-to-end execution', fg='green')


if __name__ == "__main__":
    main()