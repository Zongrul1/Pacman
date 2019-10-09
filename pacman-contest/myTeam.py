# myTeam.py
# ---------
# Licensing Information:  You are free to use or extend these projects for
# educational purposes provided that (1) you do not distribute or publish
# solutions, (2) you retain this notice, and (3) you provide clear
# attribution to UC Berkeley, including a link to http://ai.berkeley.edu.
# 
# Attribution Information: The Pacman AI projects were developed at UC Berkeley.
# The core projects and autograders were primarily created by John DeNero
# (denero@cs.berkeley.edu) and Dan Klein (klein@cs.berkeley.edu).
# Student side autograding was added by Brad Miller, Nick Hay, and
# Pieter Abbeel (pabbeel@cs.berkeley.edu).

import sys

sys.path.append("teams/L.D.S/")
from captureAgents import CaptureAgent
import random, time, util
from game import Directions
import game
from captureAgents import CaptureAgent
import random, time, util
import math
from game import Directions, Actions
import copy
import game
from util import nearestPoint


#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first='OffensiveDummyAgent', second='DefensiveDummyAgent'):
    """
  This function should return a list of two agents that will form the
  team, initialized using firstIndex and secondIndex as their agent
  index numbers.  isRed is True if the red team is being created, and
  will be False if the blue team is being created.

  As a potentially helpful development aid, this function can take
  additional string-valued keyword arguments ("first" and "second" are
  such arguments in the case of this function), which will come from
  the --redOpts and --blueOpts command-line arguments to capture.py.
  For the nightly contest, however, your team will be created without
  any extra arguments, so you should make sure that the default
  behavior is what you want for the nightly contest.
  """

    # The following line is an example only; feel free to change it.
    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########
SAFE_FODD_REMAIN = 4
FORCED_DEFEND_TICK = 4


class DummyAgent(CaptureAgent):
    """
  A Dummy agent to serve as an example of the necessary agent structure.
  You should look at baselineTeam.py for more details about how to
  create an agent as this is the bare minimum.
  """

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.start = gameState.getAgentPosition(self.index)
        self.home = gameState.getAgentState(self.index).getPosition()  # return
        self.walls = gameState.getWalls().asList()  # walls
        self.initFood = self.getFoodYouAreDefending(gameState).asList()
        self.init_defend = True  # 20190926
        self.eatenFood = []
        '''
    Your initialization code goes here, if you need any.
    '''

    def getSuccessors(self, currentPosition):
        successors = []
        forbidden = self.walls
        for action in [Directions.NORTH, Directions.SOUTH, Directions.EAST, Directions.WEST]:
            x, y = currentPosition
            dx, dy = Actions.directionToVector(action)
            nx, ny = int(x + dx), int(y + dy)
            if (nx, ny) not in forbidden:
                nextPosition = (nx, ny)
                successors.append((nextPosition, action))
        return successors
    # get middle
    def getMiddle(self, gameState):
        if self.red:
            middle = [((gameState.data.layout.width / 2) - 1, y) for y in range(0, gameState.data.layout.height)]
        else:
            middle = [(gameState.data.layout.width / 2, y) for y in range(0, gameState.data.layout.height)]
        availableMiddle = [a for a in middle if a not in self.walls]
        return availableMiddle
    # get closemiddle
    def getCloseMiddle(self, gameState):
        if self.red:
            middle = [((gameState.data.layout.width / 2) - 1, y) for y in range(0, gameState.data.layout.height)]
        else:
            middle = [(gameState.data.layout.width / 2, y) for y in range(0, gameState.data.layout.height)]
        availableMiddle = [a for a in middle if a not in self.walls]
        #20191009
        enemy = self.getDefender(gameState)
        middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), mi) for mi in availableMiddle]
        weight = 1000
        if enemy is not None and enemy[0].scaredTimer < 9:  # position of enemy 20190926
            if len(enemy) == 1:
                middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) + weight / (
                            self.getMazeDistance(enemy[0].getPosition(), a) + 0.001) for a in middle]
            else:
                middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) + weight / (
                            self.getMazeDistance(enemy[0].getPosition(), a) + 0.001) +
                                weight / (self.getMazeDistance(enemy[1].getPosition(), a) + 0.001) for a in middle]
        closeMiddle = [m for m, d in zip(middle, middleDis) if d == min(middleDis)]
        return closeMiddle

    # get condition of enemies
    def getOffender(self, gameState):
        enemies = [gameState.getAgentState(o) for o in self.getOpponents(gameState)]
        offerders = [a for a in enemies if a.isPacman and a.getPosition() is not None]
        if len(offerders) == 0:
            return None
        else:
            return offerders

    def getDefender(self, gameState):
        enemies = [gameState.getAgentState(o) for o in self.getOpponents(gameState)]
        defenders = [a for a in enemies if a.getPosition() is not None and not a.isPacman]
        if len(defenders) == 0:
            return None
        else:
            return defenders

    # capsule-search 20190918
    def getcloseCapsule(self, gameState):
        capsules = self.getCapsules(gameState)
        if len(capsules) == 0:
            return None
        else:
            capsuleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), c) for c in capsules]
            closeCapsules = [c for c, d in zip(self.getCapsules(gameState), capsuleDis) if d == min(capsuleDis)]
            return closeCapsules[0]

    # food-search 20190918
    def getCloseFood(self, gameState):
        foods = [food for food in self.getFood(gameState).asList()]
        enemy = self.getDefender(gameState)
        foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) for a in foods]
        weight = 500
        if enemy is not None and enemy[0].scaredTimer < 9:  # position of enemy 20190926
            if len(enemy) == 1:
                foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) + weight / (
                            self.getMazeDistance(enemy[0].getPosition(), a) + 0.001) for a in foods]
            else:
                foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) + weight / (
                            self.getMazeDistance(enemy[0].getPosition(), a) + 0.001) +
                                weight / (self.getMazeDistance(enemy[1].getPosition(), a) + 0.001) for a in foods]
        closeFood = [f for f, d in zip(foods, foodDistance) if d == min(foodDistance)]
        if len(closeFood) == 0:
            return None
        else:
            return closeFood[0]

    # food-search 20190920
    def getFurtherFood(self, gameState):
        foods = [food for food in self.getFood(gameState).asList()]
        foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) for a in foods]
        closeFood = [f for f, d in zip(foods, foodDistance) if d == max(foodDistance)]
        if len(closeFood) == 0:
            return None
        else:
            return closeFood[0]

    # food-search 20190924
    def getRandomFood(self, gameState):
        foods = [food for food in self.getFood(gameState).asList()]
        foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) for a in foods]
        closeFood = [f for f, d in zip(foods, foodDistance)]
        if len(closeFood) == 0:
            return None
        else:
            return random.choice(closeFood)

    def astarSearch(self, gameState, goal, heuristic):
        PQue = util.PriorityQueue()
        visited = []
        start = self.getCurrentObservation().getAgentState(self.index).getPosition()
        PQue.push((start, []), 0)
        while not PQue.isEmpty():
            loc, path = PQue.pop()
            if loc == goal:
                if len(path) == 0:
                    return 'Stop'
                return path[0]  # move once each time
            if loc not in visited:
                visited.append(loc)
                for suc in self.getSuccessors(loc):  # pos action
                    PQue.push((suc[0], path + [suc[1]]), len(path + [suc[1]]) + heuristic(gameState, suc[0]))
        return 'Stop'

    def manhattanHeuristic(self, gameState, goal, info={}):
        "The Manhattan distance heuristic for a PositionSearchProblem"
        x1, y1 = gameState.getAgentState(self.index).getPosition()
        x2, y2 = goal
        return abs(x1 - x2) + abs(y1 - y2)

    # 20190919
    def simple_avoidEnemyHeurisitic(self, gameState, position):
        enemy = self.getDefender(gameState)
        avoid = []
        if enemy is None:
            return 0
        for e in enemy:
            if self.getMazeDistance(position, e.getPosition()) < 2:
                avoid.append(9999)
            else:
                avoid.append(0)
        return max(avoid)

    # 20190930
    def simple_avoidAllEnemyHeurisitic(self, gameState, position):
        o = self.getOffender(gameState)
        d = self.getDefender(gameState)
        if d is None and o is None:
            return 0;
        if d is None:
            enemy = o;
        elif o is None:
            enemy = d;
        else:
            enemy = o + d
        avoid = []
        for e in enemy:
            if self.getMazeDistance(position, e.getPosition()) < 2:
                avoid.append(9999)
            else:
                avoid.append(0)
        return max(avoid)

    # 20190921
    def FoodHeuristic(self, location, foodGrid):
        return 0


class OffensiveDummyAgent(DummyAgent):
    def chooseAction(self, gameState):
        closeCapsule = self.getcloseCapsule(gameState)
        foods = self.getFood(gameState).asList()
        closeFood = self.getCloseFood(gameState)
        # back to the middle
        closeMiddle = self.getMiddle(gameState)
        # no time
        if gameState.data.timeleft < 50:
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        # almost no time
        if gameState.data.timeleft < 150 and gameState.getAgentState(
                self.index).numCarrying > 0 and self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                                                     closeFood) > 3:  # if time is not enough 20190926
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        # enemy-scared
        enemy = self.getDefender(gameState)  # escape
        # scared time judge
        if enemy is not None:
            for e in enemy:
                if e.scaredTimer > 9:
                    return self.astarSearch(gameState, closeFood, self.FoodHeuristic)
        # capsule improve at 20191009
        if closeCapsule is not None:
            if enemy is not None:
                for e in enemy:
                    if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                                             closeCapsule) < 5:
                        if self.getMazeDistance(closeCapsule,
                                        e.getPosition()) > 2:
                            return self.astarSearch(gameState, closeCapsule, self.simple_avoidEnemyHeurisitic)
        # enemy
        if enemy is not None:
            for e in enemy:
                if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                        e.getPosition()) < 3 and gameState.getAgentState(self.index).numCarrying > 1:#20191009 test
                    return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        # almost win
        if len(self.getFood(gameState).asList()) <= 2:
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        # carry too much
        if gameState.getAgentState(self.index).numCarrying > 1 and self.getMazeDistance(
                gameState.getAgentState(self.index).getPosition(), closeFood) > 5 and enemy is not None:
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        else:  # food 20190919
            if foods is not None:
                if gameState.getAgentState(self.index).scaredTimer > 0:  # when scared avoid invader 20190930
                    return self.astarSearch(gameState, closeFood, self.simple_avoidAllEnemyHeurisitic)
                else:
                    return self.astarSearch(gameState, closeFood, self.simple_avoidEnemyHeurisitic)
            else:
                return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)


class DefensiveDummyAgent(DummyAgent):
    def chooseAction(self, gameState):
        # back to the middle
        closeMiddle = self.getMiddle(gameState)
        # defendence
        actions = gameState.getLegalActions(self.index)
        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        closeFood = self.getCloseFood(gameState)
        # 20191004 steal
        o_enemy = self.getOffender(gameState)  # escape
        d_enemy = self.getDefender(gameState)
        if o_enemy is None:
            if d_enemy is not None:
                for e in d_enemy:
                    if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                            e.getPosition()) < 3:
                        return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
            if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), closeFood) < 6:#20191009 test
                return self.astarSearch(gameState, closeFood, self.simple_avoidEnemyHeurisitic)
        foodLeft = len(self.getFood(gameState).asList())

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction

        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        features = self.getFeatures(gameState, action)
        weights = self.getWeights(gameState, action)
        return features * weights

    def getFeatures(self, gameState, action):
        features = util.Counter()
        successor = self.getSuccessor(gameState, action)

        myState = successor.getAgentState(self.index)
        myPos = myState.getPosition()

        # Computes whether we're on defense (1) or offense (0)
        features['onDefense'] = 1
        if myState.isPacman: features['onDefense'] = 0

        # Computes distance to invaders we can see
        enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
        invaders = [a for a in enemies if a.isPacman and a.getPosition() != None]
        features['numInvaders'] = len(invaders)
        if len(invaders) > 0:
            dists = [self.getMazeDistance(myPos, a.getPosition()) for a in invaders]
            features['invaderDistance'] = min(dists)
        # if myState.scaredTimer > 0 and features['invaderDistance'] < 2:
        # features['invaderDistance'] = -features['invaderDistance']

        # Computes distance to lost food 20190926
        foodList = self.getFoodYouAreDefending(gameState).asList()
        if len(self.initFood) - len(foodList) > 0:
            self.eatenFood += (list(set(self.initFood).difference(set(foodList))))
            self.initFood = foodList
        if len(self.eatenFood) > 0:
            dists = self.getMazeDistance(myPos, self.eatenFood[-1])  # latest eatenfood
            features['eatenFood'] = dists
            if (myPos == self.eatenFood[-1]):
                self.eatenFood = []  # 20190930 clear eatenFood list to back to the middle

        if action == Directions.STOP: features['stop'] = 1
        rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == rev: features['reverse'] = 1

        middle = self.getMiddle(gameState)  # init defence
        features["Middle"] = self.getMazeDistance(myPos, middle[int(len(middle) / 2)])
        return features

    def getWeights(self, gameState, action):
        return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'eatenFood': -5, 'stop': -100,
                'reverse': -2, 'Middle': -3}
