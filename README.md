# SocialNetworkIPProblem
Usage
<ol>
<li> Install python3 (sudo apt-get install python3)
<li> Install cplex (https://www-01.ibm.com/software/websphere/products/optimization/cplex-studio-community-edition/)
<li> Install the python package in cplex (in directory /opt/ibm/..../cplex/python/3.4/x86-64_linux/setup.py)
<li> Run random_graph_generator.py to generate graph. Run random_graph_generator.py with -h for more information
<li> That would have generated a list of edges separated by newlines in a file 
<li> Use that file or any other file of the same format to run ip_project.py. Check -h for details.
<li> Open the output.txt for the solution
</ol>
