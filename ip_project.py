import argparse
import cplex
from cplex.exceptions import CplexError


def load(file):
    edges = {}
    n = 0
    with open(file) as f:
        for line in f:
            i,j = map( lambda item: int(item), line.split())
            try:
                edges[i] += [j]
            except KeyError:
                edges[i] = [j]
            try:
                edges[j] += [i]
            except KeyError:
                edges[j] = [i]
            n += 1
    return (edges,n)

def build_model(edges,n,M,m):
    ''' Builds the IP model use cplex.
    
    edge: a dict of id representing the edges {i:j}
    n : number of nodes in graph
    M : required number of people we need at the end
    m : number of friends needed to influence someone to install the app
    '''
    model = cplex.Cplex()
    
    # create variables
    
    # x[i,j] is 1 if app installed at step j else 0
    x = []
    x_names = []
    for i in range(n):
        x.append([])
        for j in range(n):
            name = 'x['+str(i)+','+str(j)+']'
            x_names.append(name)
            x[i].append(name)
    model.variables.add(names=x_names, lb=[0]*n**2, ub=[1]*n**2, types=['B']*n**2)
    
    # y[i,j] is 1 if i has at least m friends who have the app installed at step j-1 else 0
    y = []
    y_names = []
    for i in range(n):
        y.append([])
        for j in range(n):
            name = 'y['+str(i) +','+str(j)+']'
            y_names.append(name)
            y[i].append(name)
    model.variables.add(names=y_names, lb=[0]*n**2, ub=[1]*n**2, types=['B']*n**2)

    # d is the deviation from the absolute target
    model.variables.add(names=['d'], lb=[0], ub=[n-M])
    
    # construct the parameter c 
    # c[i,j] is 1 if i is friends with j else 0
    c = [[0]*n for i in range(n)]
    index = {}
    counter = 0
    for i,neighbours in edges.items():
        for j in neighbours:
            if i not in edges.keys():
                index[i] = counter
                counter += 1
            if j not in edges.keys():
                index[j] = counter
                counter += 1
    for i,neighbours in edges.items():
        for j in neighbours:
            try:
                c[index[i]][index[j]] = 1
            except: 
                pass
    
    # add constraints
    
    # Constraint 1
    # at least M people at the end
    # sum of x[i][n] for i from 0 to n-1 >= M
    
    model.linear_constraints.add(lin_expr   = [cplex.SparsePair(ind=['x['+str(i)+','+str(n-1)+']' for i in range(n)],val=[1]*n)],
                                 senses     = ['G'],
                                 rhs        = [M],
                                 names      = ['RequiredNumberOfPeople']
                                )
    
    # Constraint 2
    # as many people as possible at the end
    # d + sum of x[i][n] for i from 0 to n-1 = n
    
    model.linear_constraints.add(lin_expr    = [cplex.SparsePair(ind=['d']+['x['+str(i)+','+str(n-1)+']' for i in range(n)], val=[1]*(n+1))],
                                 senses      = ['E'], 
                                 rhs         = [n],
                                 names       = ['InfectAsManyPeopleAsPossible']
                                )
    
    # Constraint 3
    # if person i has the app installed at period t then he has it installed for the period t+1
    # x[i][t-1] <= x[i][t] for all i = 0,...,n-1 and t = 1,...,n-1
    
    model.linear_constraints.add(lin_expr   = [cplex.SparsePair(ind=['x['+str(i)+','+str(t)+']', 'x['+str(i)+','+str(t-1)+']'], val=[-1,1]) for i in range(n) for t in range(1,n)],
                                 senses     = ['L']*(n*(n-1)),
                                 rhs        = [0]*(n*(n-1)),
                                 names      = ['AppWillHauntYouForever_'+str(i) for i in range(n*(n-1)) ]
                                )
    # Constraint 4
    # if person i has at least m friends who have the app installed at time t-1 or earlier then person i will install app at time t
    # x[i][t] <= x[i][t-1] + y[i][t] 
    
    model.linear_constraints.add(lin_expr   = [cplex.SparsePair(ind=['x['+str(i)+','+str(t)+']', 'x['+str(i)+','+str(t-1)+']', 'y['+str(i)+','+str(t)+']'], val=[1,-1,-1]) for i in range(n) for t in range(1,n)],
                                 senses     = ['L']*(n*(n-1)),
                                 rhs        = [0]*(n*(n-1)),
                                 names      = ['PeerPressure_'+str(i) for i in range(n*(n-1))]
                                )
    
    # Constraint 5
    # link x[i][j] and y[i][j]
    # part A
    # sum of c[i][k] * x[k][j-1] for k from 0 to n-1 >= m * y[i][j] for all i=0,...,n-1 and j=1,...,n-1
    
    model.linear_constraints.add(lin_expr    = [cplex.SparsePair(ind=['y['+str(i)+','+str(j)+']']+['x['+str(k)+','+str(j-1)+']' for k in range(n)], val=[-m]+[c[i][k] for k in range(n)]) for i in range(n) for j in range(1,n)],
                                 senses      = ['G']*(n*(n-1)), 
                                 rhs         = [0]*(n*(n-1)),
                                 names       = ['Link1_'+str(i) for i in range(n*(n-1))]
                                )
    
    # part B
    # sum of c[i][k] * x[k][j-1] for k from 0 to n-1 <= m-1 + (n-m+1)*y[i][j] for all i=0,...,n-1 and j=1,...,n-1
    
    model.linear_constraints.add(lin_expr    = [cplex.SparsePair(ind=['y['+str(i)+','+str(j)+']']+['x['+str(k)+','+str(j-1)+']' for k in range(n)], val=[-(n-m+1)]+[c[i][k] for k in range(n)]) for i in range(n) for j in range(1,n)],
                                 senses      = ['L']*(n*(n-1)), 
                                 rhs         = [m-1]*(n*(n-1)),
                                 names       = ['Link2_'+str(i) for i in range(n*(n-1))]
                                )
    
    # Objective function
    # min weight1 * sum x[i][0] for i from 0 to n-1 + weight2 * d
    # let weight2 = 1 and weight1 = 1 + n - M
    # note: d has range from 0 to n-M 
    model.objective.set_sense(model.objective.sense.minimize)
    w1 = 1+n-M
    w2 = 1
    model.objective.set_linear('d', w2)
    for i in range(n):
        model.objective.set_linear('x['+str(i)+',0]', w1)

    print('finished modeling')
    return model

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Solve a advertisement spreading over social network problem')
    parser.add_argument('m', type=int, help='minimum number of friends needed to coerce an install')
    parser.add_argument('M', type=int, help='minimum number of people who we want to have installed the app')
    parser.add_argument('friends_file', help='file defining the social network')
    parser.add_argument('-o', '--output', help='name the output file (default: solution.txt)')
    parser.add_argument('-m', '--model', help='save the model (after running solve) to a file')
    args = parser.parse_args()
    # extract user input
    m, M, friends_file = args.m, args.M, args.friends_file
    solution_file = args.output if args.output else 'solution.txt'
    model_file = args.model if args.model else None
    edges,n = load(friends_file)
    
    # build the model
    model = build_model(edges,n,M,m)
    
    # solve the model
    model.solve()
    
    # save model to storage
    if model_file:
        model.write(model_file)
        
    # print the solution
    sol = model.solution
    print("Solution status = ", sol.get_status(), ":", end=' ')
    print(sol.status[sol.get_status()])
    if sol.is_primal_feasible():
        print("Solution value  = ", sol.get_objective_value())
        sol.write(solution_file)
        print('Solution has been written to '+solution_file)
        
        # read solution file
        import xml.etree.ElementTree as ET
        tree = ET.parse(solution_file)
        root = tree.getroot()
        for variable in root.find('variables'):
            if 'x' in variable.get('name') and ',0]' in variable.get('name'):
                print(variable.get('name') +' : '+variable.get('value'))
                
    else:
        print("No solution available.")