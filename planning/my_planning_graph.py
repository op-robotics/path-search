
from itertools import chain, combinations
from aimacode.planning import Action
from aimacode.utils import expr

from layers import BaseActionLayer, BaseLiteralLayer, makeNoOp, make_node


class ActionLayer(BaseActionLayer):

    def _inconsistent_effects(self, actionA, actionB):
        """ Return True if an effect of one action negates an effect of the other

        Hints:
            (1) `~Literal` can be used to logically negate a literal
            (2) `self.children` contains a map from actions to effects

        See Also
        --------
        layers.ActionNode
        """
        ##
        # TODO: implement this function
        ##
        ##--- iterate over each actionA's effects (literal A) and 
        ##--- locate its possible negated equivalent ~A in actionB's effects
        ##--- if found return True
        for A in self.children[actionA]:
            if ~A in self.children[actionB]:
                return True
        #--- no negation is found:        
        return False
        #raise NotImplementedError


    def _interference(self, actionA, actionB):
        """ Return True if the effects of either action negate the preconditions of the other 

        Hints:
            (1) `~Literal` can be used to logically negate a literal
            (2) `self.parents` contains a map from actions to preconditions
        
        See Also
        --------
        layers.ActionNode
        """
        # TODO: implement this function
        ##
        # discover if a negated literal ~A exists in 
        # actionB's preconditions for every one
        # of actionA's effects (literal A)  
        # if discovered, confirm interference by 
        # returning True
        for A in self.children[actionA]:
            if ~A in self.parents[actionB]:
                return True
        ##
        # discover if a negated literal ~B exists in 
        # actionA's preconditions for every one
        # of actionB's effects (literal B) 
        for B in self.children[actionB]:
            if ~B in self.parents[actionA]:
                return True
        
        return False # no interference is found
        #raise NotImplementedError
    
    def _competing_needs(self, actionA, actionB):
        """ Return True if any preconditions of the two actions are pairwise mutex in the parent layer

        Hints:
            (1) `self.parent_layer` contains a reference to the previous literal layer
            (2) `self.parents` contains a map from actions to preconditions
        
        See Also
        --------
        layers.ActionNode
        layers.BaseLayer.parent_layer
        """
        # TODO: implement this function
        #--- verify if any (A, B) combination of both actionA and actionB
        #--- preconditions is mutex or mutually excluding
        #--- return True if one such combination is found   
        for A in self.parents[actionA]:
            for B in self.parents[actionB]:
                                
                if self.parent_layer.is_mutex(A, B):
                                   
                    return True
        
        return False
        #raise NotImplementedError


class LiteralLayer(BaseLiteralLayer):

    def _inconsistent_support(self, literalA, literalB):
        """ Return True if all ways to achieve both literals are pairwise mutex in the parent layer

        Hints:
            (1) `self.parent_layer` contains a reference to the previous action layer
            (2) `self.parents` contains a map from literals to actions in the parent layer

        See Also
        --------
        layers.BaseLayer.parent_layer
        """
        # TODO: implement this function
        #--- verify if all (A, B) combinations of both literalA and literalB
        #--- are mutex or mutually excluding in the preceding layer
        #--- return True if this is the case   
        
        for A in self.parents[literalA]:
            for B in self.parents[literalB]:
                if not self.parent_layer.is_mutex(A, B):
                    ###--- when two non mutex literals are found 
                    return False
        
        return True
        #raise NotImplementedError

    def _negation(self, literalA, literalB):
        """ Return True if two literals are negations of each other """
        # TODO: implement this function
        return literalA == ~literalB
        #raise NotImplementedError


class PlanningGraph:
    def __init__(self, problem, state, serialize=True, ignore_mutexes=False):
        """
        Parameters
        ----------
        problem : PlanningProblem
            An instance of the PlanningProblem class

        state : tuple(bool)
            An ordered sequence of True/False values indicating the literal value
            of the corresponding fluent in problem.state_map

        serialize : bool
            Flag indicating whether to serialize non-persistence actions. Actions
            should NOT be serialized for regression search (e.g., GraphPlan), and
            _should_ be serialized if the planning graph is being used to estimate
            a heuristic
        """
        self._serialize = serialize
        self._is_leveled = False
        self._ignore_mutexes = ignore_mutexes
        self.goal = set(problem.goal)

        # make no-op actions that persist every literal to the next layer
        no_ops = [make_node(n, no_op=True) for n in chain(*(makeNoOp(s) for s in problem.state_map))]
        self._actionNodes = no_ops + [make_node(a) for a in problem.actions_list]
        
        # initialize the planning graph by finding the literals that are in the
        # first layer and finding the actions they they should be connected to
        literals = [s if f else ~s for f, s in zip(state, problem.state_map)]
        layer = LiteralLayer(literals, ActionLayer(), self._ignore_mutexes)
        layer.update_mutexes()
        self.literal_layers = [layer]
        self.action_layers = []

    def h_levelsum(self):
        """ Calculate the level sum heuristic for the planning graph

        The level sum is the sum of the level costs of all the goal literals
        combined. The "level cost" to achieve any single goal literal is the
        level at which the literal first appears in the planning graph. Note
        that the level cost is **NOT** the minimum number of actions to
        achieve a single goal literal.
        
        For example, if Goal_1 first appears in level 0 of the graph (i.e.,
        it is satisfied at the root of the planning graph) and Goal_2 first
        appears in level 3, then the levelsum is 0 + 3 = 3.

        Hints
        -----
          (1) See the pseudocode folder for help on a simple implementation
          (2) You can implement this function more efficiently than the
              sample pseudocode if you expand the graph one level at a time
              and accumulate the level cost of each goal rather than filling
              the whole graph at the start.

        See Also
        --------
        Russell-Norvig 10.3.1 (3rd Edition)
        """
        # TODO: implement this function
        
        # level of literal layer
        # start at 1st level    
        level = 0
        # level sum 
        levelsum = 0
        # store encountered goals here
        goals_found = set()
        # number of literal goals in the graph
        no_of_goals = len(self.goal)
        while not self._is_leveled:
            # for each goal in graph goal literals
            for _goal_ in self.goal:
                
                # if a goal is met for the first time then insert it in goals_found set
                # and increment level sum 
                if _goal_ in self.literal_layers[level] and _goal_ not in goals_found:
                    
                    goals_found.add(_goal_)
                    levelsum += level
            
            # return level sum after every goal has been found
            if len(goals_found) == no_of_goals:
                
                return levelsum
            # else expand the graph and increment the level by one
            else:
                
                self._extend()
                level += 1
                
        #raise NotImplementedError
    
    def all_goals_met(self, literal_layer):
            """
            --- return True if all planning graph goals have been 
            --- found in the passed in literal layer of the planning graph
            --- arguments: planning graph, literal layer in the graph
            
            """
            for _goal_ in self.goal:
                
                if _goal_ not in literal_layer:
                    return False
            
            return True
    
    def goals_are_mutex(self, literal_layer):
        """
        --- return True if any combination of two goals are mutex
        --- in the passed in literal layer of the planning graph
        --- arguments: planning graph, literal layer in the graph
        """
        for _goalA_ in self.goal:            
            for _goalB_ in self.goal:
               
                if literal_layer.is_mutex(_goalA_, _goalB_):
                    return True
         
        return False
    
    def h_maxlevel(self):
        """ Calculate the max level heuristic for the planning graph

        The max level is the largest level cost of any single goal fluent.
        The "level cost" to achieve any single goal literal is the level at
        which the literal first appears in the planning graph. Note that
        the level cost is **NOT** the minimum number of actions to achieve
        a single goal literal.

        For example, if Goal1 first appears in level 1 of the graph and
        Goal2 first appears in level 3, then the levelsum is max(1, 3) = 3.

        Hints
        -----
          (1) See the pseudocode folder for help on a simple implementation
          (2) You can implement this function more efficiently if you expand
              the graph one level at a time until the last goal is met rather
              than filling the whole graph at the start.

        See Also
        --------
        Russell-Norvig 10.3.1 (3rd Edition)

        Notes
        -----
        WARNING: you should expect long runtimes using this heuristic with A*
        """
        # TODO: implement maxlevel heuristic
        ###
        ## check if the last literal layer contains all graph goals          
        ## by calling all_goals_met() function.
        ## The h_maxlevel function iterates until it reaches the layer within 
        ## which all literal goals are contained and this layer also happens    
        ## to be the one that is the max (deepest) level at which one of the literals
        ## first appears in the planning graph. 
        ###
        
        # level counter
        level = 0
        while not self._is_leveled: # keep expanding the graph until it is leveled
            # does the last literal level contain all goals?            
            if self.all_goals_met(self.literal_layers[level]):
                
                return level  #maxlevel is found
            else:
                # if the last level has some missing goals  
                # add one more layer to the existing graph
                self._extend()
            # increment layer level by one
            level += 1
        
        #raise NotImplementedError

    def h_setlevel(self):
        """ Calculate the set level heuristic for the planning graph

        The set level of a planning graph is the first level where all goals
        appear such that no pair of goal literals are mutex in the last
        layer of the planning graph.

        Hints
        -----
          (1) See the pseudocode folder for help on a simple implementation
          (2) You can implement this function more efficiently if you expand
              the graph one level at a time until you find the set level rather
              than filling the whole graph at the start.

        See Also
        --------
        Russell-Norvig 10.3.1 (3rd Edition)

        Notes
        -----
        WARNING: you should expect long runtimes using this heuristic on complex problems
        """
        # TODO: implement setlevel heuristic
         
        level = 0
        
        while not self._is_leveled:
            
            # if the last layer holds all the goals
            if self.all_goals_met(self.literal_layers[level]):
                # then look for any pair of goal literals that are mutex
                # check for mutex pairs in -goals_are_mutex- function 
                if self.goals_are_mutex(self.literal_layers[level]):
                    # if mutex pair is found: 
                    # continue iteration by expanding the graph 
                    self._extend()
                    level += 1
                 
                else:
                    # return layer level if all goals have been seen
                    # and there are no mutex pair of goal literals
                    return level
            # if a goal/goals are missing in the last layer
            # continue by expanding the graph
            else:
                
                self._extend()
                level += 1
         
         #raise NotImplementedError

    ##############################################################################
    #                     DO NOT MODIFY CODE BELOW THIS LINE                     #
    ##############################################################################

    def fill(self, maxlevels=-1):
        """ Extend the planning graph until it is leveled, or until a specified number of
        levels have been added

        Parameters
        ----------
        maxlevels : int
            The maximum number of levels to extend before breaking the loop. (Starting with
            a negative value will never interrupt the loop.)

        Notes
        -----
        YOU SHOULD NOT THIS FUNCTION TO COMPLETE THE PROJECT, BUT IT MAY BE USEFUL FOR TESTING
        """
        while not self._is_leveled:
            if maxlevels == 0: break
            self._extend()
            maxlevels -= 1
        return self

    def _extend(self):
        """ Extend the planning graph by adding both a new action layer and a new literal layer

        The new action layer contains all actions that could be taken given the positive AND
        negative literals in the leaf nodes of the parent literal level.

        The new literal layer contains all literals that could result from taking each possible
        action in the NEW action layer. 
        """
        if self._is_leveled: return

        parent_literals = self.literal_layers[-1]
        parent_actions = parent_literals.parent_layer
        action_layer = ActionLayer(parent_actions, parent_literals, self._serialize, self._ignore_mutexes)
        literal_layer = LiteralLayer(parent_literals, action_layer, self._ignore_mutexes)

        for action in self._actionNodes:
            # actions in the parent layer are skipped because are added monotonically to planning graphs,
            # which is performed automatically in the ActionLayer and LiteralLayer constructors
            if action not in parent_actions and action.preconditions <= parent_literals:
                action_layer.add(action)
                literal_layer |= action.effects

                # add two-way edges in the graph connecting the parent layer with the new action
                parent_literals.add_outbound_edges(action, action.preconditions)
                action_layer.add_inbound_edges(action, action.preconditions)

                # # add two-way edges in the graph connecting the new literaly layer with the new action
                action_layer.add_outbound_edges(action, action.effects)
                literal_layer.add_inbound_edges(action, action.effects)

        action_layer.update_mutexes()
        literal_layer.update_mutexes()
        self.action_layers.append(action_layer)
        self.literal_layers.append(literal_layer)
        self._is_leveled = literal_layer == action_layer.parent_layer
