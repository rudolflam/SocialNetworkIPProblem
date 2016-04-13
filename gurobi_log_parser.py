import argparse
def parse(filename):
    print( 'Parsing '+filename)

    with open(filename) as file:
        for line in file:
            if not line.startswith(' Expl Unexpl |  Obj  Depth IntInf | Incumbent    BestBd   Gap | It/Node Time'):
                continue
            else:
                break
        for line in file:
            if line.strip == '':
                continue
            else:
                break
        lastline = ''
        steps = 0
        for line in file:
            if line.strip() == '':
                break
            else:
                steps += 1
                lastline = line
        data = lastline.split()
        try:
            explored_nodes = int(data[0])
        except:
            data = data[1:]
            explored_nodes = int(data[0])
        time = int(data[-1][:-1])
        return {'steps': steps, 'explored nodes': explored_nodes, 'time' : time}
        
if __name__=='__main__':
    parser = argparse.ArgumentParser(description='Parses a gurobi log file')
    parser.add_argument('filename', help='The log file')
    
    args = parser.parse_args()
    
    print( parse(args.filename) )
