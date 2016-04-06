import random_graph_generator
import argparse
from subprocess import call

def run(I, n, m, M, greedy):
    for i in range(I):
        # create a random graph and write it to random_graph_i.txt
        greedy_str = 'greedy' if greedy else ''
        filename = 'random_graph_'+str(i)+'_'+greedy_str+'.txt'
        sol_filename = 'random_graph_'+str(i)+'_'+greedy_str+'_solution.txt'
        log_filename = 'random_graph_'+str(i)+'_'+greedy_str+'_log.txt'
        random_graph_generator.generate( filename, n)
        greedy_opt = '--greedy' if greedy else ' '
        # read the file to optimizer
        call('gurobi.sh gurobi_ip_project.py '+str(m)+' '+ str(M)+' '+filename+' -o '+sol_filename+' -l '+log_filename+' '+greedy_opt, shell=True)
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Generate n random undirected social network graphs and then solve to find minimum number of people to infect M people after n iterations')
    parser.add_argument('I', type=int, help='number of iterations (min 1)')
    parser.add_argument('n', type=int, help='number of people (min 2)')
    parser.add_argument('m', type=int, help='minimum number of friends needed to coerce an install')
    parser.add_argument('M', type=int, help='minimum number of people who we want to have installed the app')
    parser.add_argument('--greedy', action='store_true', help='seed the problem with an initial feasible solution using greedy algorithm')

    args = parser.parse_args()
    
    I, n, m, M = args.I, args.n, args.m, args.M
    run(I, n, m, M, True)
    run(I, n, m, M, False)
    