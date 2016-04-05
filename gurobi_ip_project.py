from gurobipy import *
import argparse

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
    ''' Builds the IP model use gurobi.
    
    edge: a dict of id representing the edges {i:j}
    n : number of nodes in graph
    M : required number of people we need at the end
    m : number of friends needed to influence someone to install the app
    '''
    
    # create the model
    model = Model("Social Network Cascade")
    
    print('Initiating model')
    
    # create the variables
    # x[i,j] is 1 if app installed at step j else 0
    # y[i,j] is 1 if i has at least m friends who have the app installed at step j-1 else 0
    x = []
    y = []
    for i in range(n):
        x.append([])
        y.append([])
        for j in range(n):
            x_name = 'x['+str(i)+','+str(j)+']'
            x[i].append(model.addVar(vtype=GRB.BINARY, name=x_name))
            y_name = 'y['+str(i) +','+str(j)+']'
            y[i].append(model.addVar(vtype=GRB.BINARY, name=y_name))
            
    # d is the deviation from the absolute target
    d = model.addVar(lb=0, ub=n-M, name='d')
    
    # choice is a disjunction variable
    choice = model.addVar(vtype=GRB.BINARY, name='choice')
    
    print('Constructed variables for model')
    
    # integrate the variables into the model
    model.update()
    
    print('Pushed variables into model')
    
    # construct the parameter c 
    # c[i,j] is 1 if i is friends with j else 0
    c = [[0]*n for i in range(n)]
    # create an index to re-enumerate the ids
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
    
    print('Loaded friends web')
    
    # calculate the number of friends for each person
    # and calculate if each person has less than m friends
    f = [0]*n
    ltm = [0]*n
    for i, neighbours in edges.items():
        f[i] = len(neighbours)
        ltm[i] = 1 if f[i] < m else 0
    
    # add constraints
    
    print('Loading constraints')
    
    def summation(list):
        return reduce(lambda acc,a: acc+a, list)
    # Constraint 1
    # at least M people at the end
    # sum of x[i][n-1] for i from 0 to n-1 >= M
    
    model.addConstr( summation([x[i][n-1] for i in range(n)]) >= M, 'RequiredNumberOfPeople' )
    print('Loaded constraint 1')
    
    # Constraint 2
    # as many people as possible at the end
    # d + sum of x[i][n-1] for i from 0 to n-1 = n
    
    model.addConstr( d+summation([x[i][n-1] for i in range(n)]) == n , 'InfectAsManyPeopleAsPossible')
    print('Loaded constraint 2')
    
    # Constraint 3
    # if person i has the app installed at period t then he has it installed for the period t+1
    # x[i][t-1] <= x[i][t] for all i = 0,...,n-1 and t = 1,...,n-1
    
    for i in range(n) :
        for t in range(1,n):
            model.addConstr( x[i][t-1] <= x[i][t], 'AppWillHauntYouForever')
    print('Loaded constraint 3')
    
    # Constraint 4
    # if person i has at least m friends who have the app installed at time t-1 or earlier then person i will install app at time t
    # x[i][t] <= x[i][t-1] + y[i][t] for all i = 0,...,n-1 and t = 1,...,n-1
    
    for i in range(n):
        for t in range(1,n):
            model.addConstr( x[i][t] <= x[i][t-1] + y[i][t], 'PeerPressure')
    print('Loaded constraint 4')
    
    # Constraint 5
    # link x[i][j] and y[i][j]
    # part A
    # sum of c[i][k] * x[k][j-1] for k from 0 to n-1 >= m * y[i][j] for all i=0,...,n-1 and j=1,...,n-1
    
    for i in range(n):
        for t in range(1,n):
            model.addConstr( summation([c[i][j] * x[j][t-1] for j in range(n)]) >= m * y[i][t], 'Link1' )
    print('Loaded constraint 5A')
    
    # part B
    # sum of c[i][k] * x[k][j-1] for k from 0 to n-1 <= m-1 + (n-m+1)*y[i][j] for all i=0,...,n-1 and j=1,...,n-1
    
    for i in range(n):
        for t in range(1,n):
            model.addConstr( summation([c[i][k] * x[k][t-1] for k in range(n)]) <= m-1+ (n-m+1) * y[i][t], 'Link2' )
    print('Loaded constraint 5B')
    
    # Constraint 6
    # we require a minimum of m people to seed the process
    # sum of x[i][0] >= m
    
    model.addConstr( summation([x[i][0] for i in range(n)]) >= m, 'MinimumSeed' )
    print('Loaded constraint 6')
    
    # Constraint 7
    # people who have less than m friends cannot be infected, so they either are infected on the first step or never at all
    # sum of x[i][t] for t from 0 to n-1 == (n or 0) for all i with less than m friends 
    
    for i in range(n):
        if ltm[i] == 1:
            model.addConstr( summation([x[i][t] for t in range(n)]) == n*choice , 'NeverInfected')
    print('Loaded constraint 7')
    
    # create the objective function
    # min weight1 * sum x[i][0] for i from 0 to n-1 + weight2 * d
    # let weight2 = 1 and weight1 = 1 + n - M
    # note: d has range from 0 to n-M 
    
    w1 = 1+n-M
    w2 = 1
    model.setObjective(w1 * summation([x[i][0] for i in range(n)]) + w2 * d , GRB.MINIMIZE)
    print('Loaded Objective')
    
    # flush everything into the model
    model.update()
    
    # MIP Start
    # greedy algorithm
    
    
    print('Finished building model')
    
    return model

if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Solve a advertisement spreading over social network problem')
    parser.add_argument('m', type=int, help='minimum number of friends needed to coerce an install')
    parser.add_argument('M', type=int, help='minimum number of people who we want to have installed the app')
    parser.add_argument('friends_file', help='file defining the social network')
    parser.add_argument('-o', '--output', help='name the output file (default: solution.txt)')
    parser.add_argument('-m', '--model', help='save the model (after running solve) to a file')
    parser.add_argument('--memory', action='store_true', help='activates NodefileStart param at 0.5Gb to reduce memory usage')
    args = parser.parse_args()
    # extract user input
    m, M, friends_file = args.m, args.M, args.friends_file
    solution_file = args.output if args.output else 'solution.txt'
    model_file = args.model if args.model else None
    edges,n = load(friends_file)
    
    # build the model
    model = build_model(edges,n,M,m)
    model.params.NodefileStart = 0.5 if args.memory else model.params.NodefileStart
    
    # find solution
    def callback(model, where):
        print(str(model) +' called '+ str(where))
    solution =  model.optimize(callback)
    
    for v in model.getVars():
        if 'x' in v.varName and ',0]' in v.varName:
            print (v.varName+':'+str(v.x))
    for v in model.getVars():
        if 'x' in v.varName and ','+str(n-1)+']' in v.varName:
            print (v.varName+':'+str(v.x))
    print('Objective value:', model.objVal)
    