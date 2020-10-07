import sys
import copy
import time

# Running script: given code can be run with the command:
# python file.py, ./path/to/init_state.txt ./output/output.txt

class Sudoku(object):
    def __init__(self, puzzle):
        # you may add more attributes if you need
        self.puzzle = puzzle # self.puzzle is a list of lists
        self.ans = [row[:] for row in puzzle] # no need deepcopy
        self.backtrack_count = 0
        self.domains = self.generate_domains()
        self.neighbours = self.generate_neighbours()
        self.assignment = self.generate_assignment()
        self.assigned = self.generate_assigned_cells()
        self.unassigned = self.generate_unassigned_cells()
        self.pruned = {}
        self.start = -1
        self.end = -1
    
    # generate the initial domains of all the variables.
    # a variable's domain is itself is the grid position is already filled initially,
    # or else it will be in the range from 1 to 9.
    def generate_domains(self):
        domains = {}
        possible = range(1, 10)
        for i in range(9):
            for j in range(9):
                domains[(i, j)] = set(possible) if self.ans[i][j] == 0 else set([self.ans[i][j]])
        return domains

    # generate cells that are initially empty
    def generate_unassigned_cells(self):
        unassigned = set()
        for i in range(9):
            for j in range(9):
                if len(self.domains[(i, j)]) != 1:
                    unassigned.add((i, j))
        return unassigned

    # generate cells that are initially filled
    def generate_assigned_cells(self):
        assigned = set()
        for i in range(9):
            for j in range(9):
                if len(self.domains[(i, j)]) == 1:
                    assigned.add((i, j))
        return assigned

    # generate all initial assignments, which is just the cell's value itself
    def generate_assignment(self):
        assignments = {}
        for i in range(9):
            for j in range(9):
                if self.ans[i][j] != 0:
                    assignments[(i, j)] = self.ans[i][j]
        return assignments

    # generate all neighbours for each cell
    def generate_neighbours(self):
        neighbours_dict = {}
        for i in range(9):
            for j in range(9):
                neighbours_dict[(i, j)] = self.neighbour_helper_function(i, j)
        return neighbours_dict

    # helper function to calculate position and neighbours    
    def neighbour_helper_function(self, row, col):
        neighbours = set()
        for i in range(9):
            if i == row:
                continue
            neighbours.add((i, col))
        for j in range(9):
            if j == col:
                continue
            neighbours.add((row, j))
        r_row = row - row % 3
        r_col = col - col % 3
        for i in range(3):
            for j in range(3):
                if r_row + i == row and r_col + j == col:
                    continue
                neighbours.add((r_row + i, r_col + j))
        return neighbours
    
    # if a cell's value if not found in its neighbour, then it is unsatisfiable, or else false
    def satisfy(self, var, val):
        for (assigned_var, assigned_val) in self.assignment:
            if assigned_var in self.neighbours[var] and val == assigned_val:
                return False
        return True

    # assigns a value to a cell
    def assign(self, var, val):
        self.assignment[var] = val
        self.unassigned.remove(var)
        # need add domain?

    # unassigns value from a cell, removed all pruned values
    def unassign(self, var, val):
        if var in self.assignment:
            if var in self.pruned:
                for removed_value in self.pruned[var]:
                    self.domains[removed_value[0]].add(removed_value[1])
                del self.pruned[var]
            del self.assignment[var]
            self.unassigned.add(var)

    # goal test
    def done(self):
        for domain in self.domains.values():
            if len(domain) != 1:
                return False
        return True
        
########################################################################################################
    # The ac3 algorithm shrinks the domain size of each variables by checking for each assigned value, that value
    # is consistent with all the neighbours of that cell.
    def generate_ac3_queue(self):
        queue = []
        for assigned_cells in self.assigned:
            assigned_cell_neighbours = self.neighbours[assigned_cells]
            for neighbour in assigned_cell_neighbours:
                if neighbour in self.unassigned:
                    queue.append((neighbour, assigned_cells))
        return queue
    
    def ac3_2(self, queue):
        while queue:
            x_i, x_j = queue.pop(0)
            for d_j in self.domains[x_j]:
                if d_j in self.domains[x_i]:
                    self.domains[x_i].remove(d_j)
                    if len(self.domains[x_i]) == 0:
                        return False
                    elif len(self.domains[x_i]) > 1: # won't fail if > 1 domain value
                        continue
                    peers = self.neighbours[x_i]
                    for x_k in peers:
                        if x_k == x_j:
                            continue
                        queue.append((x_k, x_i))
        return True

    def revise(self, x_i, x_j):
        revised = False
        for x in self.domains[x_i]:
            if not any(x != y for y in self.domains[x_j]):
                self.domains[x_i].remove(x)
                revised = True
        return revised

    # ac3 algorithm. Refered from AIMA textbook, which maintains a queue to maintain consistent values in a pair of 
    # (X_i, X_j). Whenever a pair is revised, all the neighbours of X_j except for X_i is added back into the queue.
    def ac3(self, queue):
        while queue:
            x_i, x_j = queue.pop(0)
            if self.revise(x_i, x_j):
                if len(self.domains[x_i]) == 0:
                    return False
                for neighbour in self.neighbours[x_i]:
                    if neighbour == x_j:
                        continue
                    queue.append([neighbour, x_i])
        return True

#############################################################################################################
    def solve(self):
        self.start = time.time()
        queue = self.generate_ac3_queue()
        #for a in self.unassigned:
        #    print(self.domains[a])
        self.ac3_2(queue)
        self.fill()
        #print(self.assignment)
        if self.done():
            self.end = time.time()
            print(self.end - self.start)
            print("backtrack calls: " + str(self.backtrack_count))
            return self.ans
        self.backtrack()
        self.end = time.time()
        self.fill()
        #print(self.assignment)
        print(self.end - self.start)
        print("backtrack calls: " + str(self.backtrack_count))
        #print(self.ans)
        return self.ans
    
    def fill(self):
        for (var, domain) in self.domains.items():
            if len(domain) == 1:
                if var in self.unassigned:
                    self.unassigned.remove(var)
                self.assignment[var] = list(domain)[0]
                self.ans[var[0]][var[1]] = list(domain)[0]
        for (var, val) in self.assignment.items():
            self.ans[var[0]][var[1]] = val
#############################################################################################################
    # backtracking search algorithm, refered from AIMA textbook. Uses DFS to assign values to selected variables, 
    # and backtrack if an assignment fails.
    def backtrack(self):
        if len(self.assignment) == 81:
            return True
        self.backtrack_count += 1
        chosen = self.select_unassigned_variable()
        #self.pruned.clear()
        for val in self.order_domain_values(chosen):
            if self.satisfy(chosen, val):
                self.assign(chosen, val)
                if self.forward_check(chosen, val):
                    if self.backtrack():
                        return True
                self.unassign(chosen, val)
        return False
        
    # inference with forward checking. This algorithm uses early termination, and whenever a value is assigned,
    # removes that value from all its unassigned neighbours. If any unassigned variables have no allowed, returns false
    def forward_check(self, var, val):
        for neighbour in self.neighbours[var]:
            if val in self.domains[neighbour]:
                if var not in self.pruned:
                    self.pruned[var] = set()
                    self.pruned[var].add((neighbour, val))
                else:
                    self.pruned[var].add((neighbour, val))
                self.domains[neighbour].remove(val)
                if not self.domains[neighbour]:
                    return False
        return True
#############################################################################################################
    # the MRV(minimum remaining value heuristic). The most constrained variable has the smallest domain,
    # which is the least possible values. THe algorithm selects the unassigned variable with fewest values possible.
    def select_unassigned_variable(self):
        unassigned_list = [var for var in self.unassigned]
        return min(unassigned_list, key = lambda x: len(self.domains[x]))

    # degree heuristic
    def get_degree(self, var):
        degree = 0
        for neighbour in self.neighbours[var]:
            if neighbour not in self.assignment:
                degree += 1
        return degree
#############################################################################################################
    # the least constraining value heuristic. Each variable has a domain, and the domain that rules out the 
    # fewest values for neighbouring unassigned variables is given priority.
    def order_domain_values(self, var):
        ordered = []
        for value in self.domains[var]:
            ordered.append(value)
        return sorted(ordered, key = lambda val: self.get_conflict(var, val))

    def get_conflict(self, var, val):
        conflicts = 0
        for neighbour in self.neighbours[var]:
            if val in self.domains[neighbour]:
                conflicts += 1
        return conflicts

    # you may add more classes/functions if you think is useful
    # However, ensure all the classes/functions are in this file ONLY
    # Note that our evaluation scripts only call the solve method.
    # Any other methods that you write should be used within the solve() method.

if __name__ == "__main__":
    # STRICTLY do NOT modify the code in the main function here
    if len(sys.argv) != 3:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise ValueError("Wrong number of arguments!")

    try:
        f = open(sys.argv[1], 'r')
    except IOError:
        print ("\nUsage: python CS3243_P2_Sudoku_XX.py input.txt output.txt\n")
        raise IOError("Input file not found!")

    puzzle = [[0 for i in range(9)] for j in range(9)]
    lines = f.readlines()

    i, j = 0, 0
    for line in lines:
        for number in line:
            if '0' <= number <= '9':
                puzzle[i][j] = int(number)
                j += 1
                if j == 9:
                    i += 1
                    j = 0

    sudoku = Sudoku(puzzle)
    ans = sudoku.solve()

    with open(sys.argv[2], 'a') as f:
        for i in range(9):
            for j in range(9):
                f.write(str(ans[i][j]) + " ")
            f.write("\n")

