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
        """
    This method handles the initial setup of the
    agent to populate useful fields (such as what team
    we're on).

    A distanceCalculator instance caches the maze distances
    between each pair of positions, so your agents can use:
    self.distancer.getDistance(p1, p2)

    IMPORTANT: This method may run for at most 15 seconds.
    """

        '''
    Make sure you do not delete the following line. If you would like to
    use Manhattan distances instead of maze distances in order to save
    on initialization time, please take a look at
    CaptureAgent.registerInitialState in captureAgents.py.
    '''
        self.start = gameState.getAgentPosition(self.index)
        self.home = gameState.getAgentState(self.index).getPosition()  # return
        self.walls = gameState.getWalls().asList()  # walls
        CaptureAgent.registerInitialState(self, gameState)

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

    # get condition of enemies
    def getOffender(self, gameState):
        enemies = [gameState.getAgentState(o) for o in self.getOpponents(gameState)]
        offerder = [a for a in enemies if a.isPacman and a.getPosition() is not None]
        if len(offerder) == 0:
            return None
        else:
            return offerder

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
        enemy = self.getDefender(gameState)#escape
        foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) for a in foods]
        if enemy is not None:#position of enemy
            if len(enemy)==1:
                foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) + 100/(self.getMazeDistance(enemy[0].getPosition(), a)+0.001) for a in foods]
            else:
                foodDistance = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), a) + 100/(self.getMazeDistance(enemy[0].getPosition(), a)+0.001)+
                                100/(self.getMazeDistance(enemy[1].getPosition(), a)+0.001) for a in foods]
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
        middle = self.getMiddle(gameState)
        middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), mi) for mi in middle]
        closeMiddle = [m for m, d in zip(middle, middleDis) if d == min(middleDis)]
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

    # 20190921
    def FoodHeuristic(self, location, foodGrid):
        return 0


class OffensiveDummyAgent(DummyAgent):
    """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """

    def chooseAction(self, gameState):
        closeCapsule = self.getcloseCapsule(gameState)
        foods = self.getFood(gameState).asList()
        closeFood = self.getCloseFood(gameState)
        randomFood = self.getRandomFood(gameState)
        furtherFood = self.getFurtherFood(gameState)
        # back to the middle
        middle = self.getMiddle(gameState)
        middleDis = [self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), mi) for mi in middle]
        closeMiddle = [m for m, d in zip(middle, middleDis) if d == min(middleDis)]
        furtherMiddle = [m for m, d in zip(middle, middleDis) if d == max(middleDis)]
        enemy = self.getDefender(gameState)#escape
        if enemy is not None:#scared time judge
            for defender in enemy:
                if defender.scaredTimer > 5:
                    return self.astarSearch(gameState, closeFood, self.FoodHeuristic)
        if closeCapsule is not None and self.getMazeDistance(gameState.getAgentState(self.index).getPosition(),
                                                             closeCapsule) < 2:  # capsule
            return self.astarSearch(gameState, closeCapsule, self.simple_avoidEnemyHeurisitic)
        if enemy is not None:
            for e in enemy:
                if self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), e.getPosition()) < 2:
                    return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        if gameState.data.timeleft < 100 and gameState.getAgentState(
                self.index).numCarrying > 1:  # if time is not enough
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        if len(self.getFood(gameState).asList()) <= 2: # almost win
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        if gameState.getAgentState(self.index).numCarrying > 3 and self.getMazeDistance(gameState.getAgentState(self.index).getPosition(), closeFood) > 3:# carry too much
            return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)
        else:  # food 20190919
            if foods is not None:
                return self.astarSearch(gameState, closeFood, self.simple_avoidEnemyHeurisitic)
            else:
                return self.astarSearch(gameState, closeMiddle[0], self.simple_avoidEnemyHeurisitic)


class DefensiveDummyAgent(DummyAgent):
    def __init__(self, index):
        CaptureAgent.__init__(self, index)
        self.target = None
        self.lastTickFoodList = []
        self.isFoodEaten = False
        self.patrolDict = {}
        self.tick = 0
        self.gazeboDict = {}

    def getLayoutInfo(self, gameState):

        layoutInfo = []
        layoutWidth = gameState.data.layout.width
        layoutHeight = gameState.data.layout.height
        layoutCentralX = (layoutWidth - 2) / 2
        if not self.red:
            layoutCentralX += 1
        layoutCentralY = (layoutHeight - 2) / 2
        layoutInfo.extend((layoutWidth, layoutHeight, layoutCentralX, layoutCentralY))
        return layoutInfo

    def setDefensiveArea(self, gameState):

        layoutInfo = self.getLayoutInfo(gameState)

        self.coreDefendingArea = []
        for i in range(1, layoutInfo[1] - 1):
            if not gameState.hasWall(int(layoutInfo[2]), int(i)):
                self.coreDefendingArea.append((int(layoutInfo[2]), int(i)))

        desiredSize = layoutInfo[3]
        currentSize = len(self.coreDefendingArea)

        while desiredSize < currentSize:
            self.coreDefendingArea.remove(self.coreDefendingArea[0])
            self.coreDefendingArea.remove(self.coreDefendingArea[-1])
            currentSize = len(self.coreDefendingArea)
        while len(self.coreDefendingArea) > 2:
            # for i in range(currentSize/4):
            self.coreDefendingArea.remove(self.coreDefendingArea[0])
            self.coreDefendingArea.remove(self.coreDefendingArea[-1])
        # if  len(self.coreDefendingArea) == 2:
        # self.coreDefendingArea.remove(self.coreDefendingArea[0])

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.distancer.getMazeDistances()

        self.setDefensiveArea(gameState)

    def isForcedDefendRequired(self, gameState):
        candidateActions = []
        actions = gameState.getLegalActions(self.index)
        reversed_direction = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        actions.remove(Directions.STOP)
        if reversed_direction in actions:
            actions.remove(reversed_direction)

        for a in actions:
            new_state = gameState.generateSuccessor(self.index, a)
            if not new_state.getAgentState(self.index).isPacman:
                candidateActions.append(a)

        if len(candidateActions) == 0:
            self.tick = 0
        else:
            self.tick = self.tick + 1

        if self.tick > FORCED_DEFEND_TICK or self.tick == 0:
            candidateActions.append(reversed_direction)

        return candidateActions

    def chooseAction(self, gameState):

        currentTickFoodList = []
        currentTickFoodList = self.getFoodYouAreDefending(gameState).asList()

        mypos = gameState.getAgentPosition(self.index)
        if mypos == self.target:
            self.target = None
        # Get the cloest invader's position and set target as invader
        opponentsIndices = []
        threateningInvaderPos = []
        cloestInvaders = []
        minDistance = float("inf")

        opponentsIndices = self.getOpponents(gameState)
        for opponentIndex in opponentsIndices:
            oppent = gameState.getAgentState(opponentIndex)
            if oppent.isPacman and oppent.getPosition() != None:
                oppentPos = oppent.getPosition()
                threateningInvaderPos.append(oppentPos)

        if len(threateningInvaderPos) > 0:
            for position in threateningInvaderPos:
                distance = self.getMazeDistance(position, mypos)
                if distance < minDistance:
                    minDistance = distance
                    cloestInvaders.append(position)
            self.target = cloestInvaders[-1]

        # get the eaten food position
        else:
            if len(self.lastTickFoodList) > 0 and len(currentTickFoodList) < len(self.lastTickFoodList):
                eatenFood = set(self.lastTickFoodList) - set(currentTickFoodList)

                self.target = eatenFood.pop()

        self.lastTickFoodList = currentTickFoodList

        if self.target == None:
            if len(currentTickFoodList) <= SAFE_FODD_REMAIN:
                highPriorityFood = currentTickFoodList + self.getCapsulesYouAreDefending(gameState)
                self.target = random.choice(highPriorityFood)
            else:
                self.target = random.choice(self.coreDefendingArea)
        # evaluates candiateActions and get the best
        candidateActions = self.isForcedDefendRequired(gameState)
        goodActions = []
        fvalues = []

        for a in candidateActions:
            new_state = gameState.generateSuccessor(self.index, a)
            newpos = new_state.getAgentPosition(self.index)
            goodActions.append(a)
            fvalues.append(self.getMazeDistance(newpos, self.target))

        best = min(fvalues)
        bestActions = [a for a, v in zip(goodActions, fvalues) if v == best]
        bestAction = random.choice(bestActions)
        return bestAction
