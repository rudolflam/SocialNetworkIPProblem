import random_graph_generator
import gurobi_log_parser 
import argparse
from subprocess import call
from os import makedirs
from os import rename

def subroutine(i, n, m, M, greedy, offset, graph_filename, folder):
# create a random graph and write it to random_graph_i.txt
    print('Performing greedy '+str(greedy))
    greedy_str = 'greedy' if greedy else ''
    sol_filename = 'random_graph_'+str(i+offset)+'_'+greedy_str+'_solution'
    log_filename = 'random_graph_'+str(i+offset)+'_'+greedy_str+'_log.txt'
    greedy_opt = '--greedy' if greedy else ' '
    # read the file to optimizer
    command = 'gurobi.sh gurobi_ip_project.py '+str(m)+' '+ str(M)+' '+graph_filename+' -o '+sol_filename+' -l '+log_filename+' '+greedy_opt
    call(command, shell=True)
    if folder:
        try:
            rename(sol_filename+'.sol', folder+sol_filename)
        except:
            pass
        try:
            rename(log_filename, folder+log_filename)
        except:
            pass
    # parse log file
    data = gurobi_log_parser.parse(folder+log_filename)
    return (data['time'], data['explored nodes'], data['steps']) if data else ['Infeasible', None, None]
    
def run(I, n, m, M, offset, folder):
    if folder:
        folder = folder + '/'
        makedirs(folder)
    if M > n:
        raise Exception('M > n exception')
    greedy_stats_file = open(folder+'greedy_stats.txt', 'w')
    not_greedy_stats_file = open(folder+'not_greedy_stats.txt', 'w')
    for i in range(I):
        graph_filename = 'random_graph_'+str(i+offset)+'.txt' 
        if folder:
            graph_filename = folder+graph_filename
        random_graph_generator.generate( graph_filename, n)
        t_greedy, n_greedy, steps_greedy = subroutine(i, n, m, int(M*n), True, offset, graph_filename, folder)
        t_not_greedy, n_not_greedy, steps_not_greedy = subroutine(i, n, m, int(M*n), False, offset, graph_filename, folder)
        greedy_stats_file.write(str(t_greedy)+','+str(n_greedy)+','+str(steps_greedy)+'\n')
        not_greedy_stats_file.write(str(t_not_greedy)+','+str(n_not_greedy)+','+str(steps_not_greedy)+'\n')
    greedy_stats_file.close()
    not_greedy_stats_file.close()
    
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Generate n random undirected social network graphs and then solve to find minimum number of people to infect M people after n iterations')
    parser.add_argument('I', type=int, help='number of iterations (min 1)')
    parser.add_argument('n', type=int, help='starting number of people (min 2)')
    parser.add_argument('d', type=int, help='number of different number of people increasing from n')
    parser.add_argument('m', type=int, help='minimum number of friends needed to coerce an install')
    parser.add_argument('d_m', type=int, help='number of different minimum number of friends needed to coerce an install')
    parser.add_argument('P', type=float, help='percentage of minimum number of people who we want to have installed the app')
    parser.add_argument('offset', type=int, help='offset the file name index')
    parser.add_argument('folder', type=str, help='put all the output files in a folder')
    args = parser.parse_args()
    
    I, n1, n2, m1, m2, M, offset, folder = args.I, args.n, args.n + args.d, args.m, args.m + args.d_m, args.P, args.offset, args.folder
    for n in range(n1, n2):
        for m in range(m1, m2):
            subfolder = folder + '/n'+str(n)+'m'+str(m)
            run(I, n, m, M, offset, subfolder)
    