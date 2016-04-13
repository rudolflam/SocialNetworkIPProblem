import argparse

def generate( filename, n):
    from random import randint
    # construct matrix M to be an upper triangular matrix of an undirected graph
    M = [[0]*n for i in range(n)]
    
    
    # N = number of edges
    max_edges = n*(n-1)/2
    N = randint(int(max_edges/4), int(max_edges/3))
    E = set()
    while len(E) < N:
        k,l = 0,0
        while k == l:
            k = randint(0,n-1)
            l = randint(0,n-1)
        if k < l:
            E.add((k,l))
        else: 
            E.add((l,k))
    for e in E:
        i,j = e
    # construct the file
    with open(filename, 'w') as file:
        file.write(str(n)+'\n')
        for e in E:
            i,j = e
            file.write(str(i)+' '+str(j)+'\n')
            
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Generate a random undirected social network graph')
    parser.add_argument('n', type=int, help='number of people (min 2)')
    parser.add_argument('-o', '--output', help="set the output file's name (default: output.txt)")
    args = parser.parse_args()
    # extract arguments
    n = args.n if args.n >= 2 else 2
    filename = args.output if args.output else 'output.txt'
    
    generate( filename, n)
    
                    