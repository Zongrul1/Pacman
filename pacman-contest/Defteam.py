from captureAgents import CaptureAgent
import random, time, util
from game import Directions
from pacman import GameState
import game
from util import nearestPoint

#################
# Team creation #
#################

def createTeam(firstIndex, secondIndex, isRed,
               first = 'OffensiveReflexAgent', second = 'DefensiveReflexAgent'):
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
  return [eval(first)(firstIndex), eval(second)(secondIndex)]

##########
# Agents #
##########

class ReflexCaptureAgent(CaptureAgent):
  """
  A base class for reflex agents that chooses score-maximizing actions
  """

  def registerInitialState(self, gameState):
    self.start = gameState.getAgentPosition(self.index)
    CaptureAgent.registerInitialState(self, gameState)

  def chooseAction(self, gameState):
    """
    Picks among the actions with the highest Q(s,a).
    """
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
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
    """
    Returns a counter of features for the state
    """
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    features['successorScore'] = self.getScore(successor)
    return features

  def getWeights(self, gameState, action):
    """
    Normally, weights do not depend on the gamestate.  They can be either
    a counter or a dictionary.
    """
    return {'successorScore': 1.0}

class OffensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that seeks food. This is an agent
  we give you to get an idea of what an offensive agent might look like,
  but it is by no means the best or only way to build an offensive agent.
  """
  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    foodGrid = self.getFood(successor)
    foodList = foodGrid.asList()
    Capsule = self.getCapsules(gameState)
    Foodeaten = 40-GameState.getNumFood(gameState)
    HomeFood = gameState.getRedFood()
    HomeFoodList = HomeFood.asList()
    features['successorScore'] = -len(foodList)#self.getScore(successor)

    # Try to implement enemy aware offensive agent 09.16
    myState = successor.getAgentState(self.index)
    myPos = myState.getPosition()
    x,y=myPos
    enemies = [successor.getAgentState(i) for i in self.getOpponents(successor)]
    protectors = [a for a in enemies if (not a.isPacman) and a.getPosition() != None and (a.scaredTimer == 0 or a.scaredTimer <=3)]
    features['numProtectors'] = len(protectors)
    if len(protectors) > 0:
      dists = [self.getMazeDistance(myPos, a.getPosition()) for a in protectors]
      features['protectorsDistance'] = min(dists)
      if gameState.getAgentState(self.index).numCarrying>=2:
        myPos = successor.getAgentState(self.index).getPosition()
        HomeDistance = min([self.getMazeDistance(myPos, food) for food in HomeFoodList])
        features['GoBackHome'] = HomeDistance
      else:
        features['GoBackHome'] = 0


    # Try to go back home if food collected >=5

    #Compute distance to the nearest food
    if len(foodList) > 0: # This should always be True,  but better safe than sorry
      myPos = successor.getAgentState(self.index).getPosition()
      minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
      features['distanceToFood'] = minDistance
    if len(Capsule) >0:
      features['Capsule'] = min([self.getMazeDistance(myPos, Cap) for Cap in Capsule])
    return features

  def getWeights(self, gameState, action):
    return {'successorScore': 100, 'distanceToFood': -1, 'protectorsDistance': 100, 'numProtectors': 1000,
            'GoBackHome': -1000000, 'Capsule':-2}

  def getDis(self, pos1, pos2):
    return abs(pos1[0]-pos2[0])+abs(pos1[1]-pos2[1])

  def chooseAction(self, gameState):
    actions = gameState.getLegalActions(self.index)

    # You can profile your evaluation time by uncommenting these lines
    # start = time.time()
    values = [self.evaluate(gameState, a) for a in actions]
    # print 'eval time for agent %d: %.4f' % (self.index, time.time() - start)

    maxValue = max(values)
    bestActions = [a for a, v in zip(actions, values) if v == maxValue]

    foodLeft = len(self.getFood(gameState).asList())

    if foodLeft <= 2:
      bestDist = 9999
      for action in actions:
        successor = self.getSuccessor(gameState, action)
        pos2 = successor.getAgentPosition(self.index)
        dist = self.getMazeDistance(self.start,pos2)
        if dist < bestDist:
          bestAction = action
          bestDist = dist
      return bestAction

    return random.choice(bestActions)


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
            if suc not in visited:
              PQue.push((suc[0], path + [suc[1]]), len(path + [suc[1]]) + heuristic(gameState,loc, suc[0]))
      return 'Stop'



class DefensiveReflexAgent(ReflexCaptureAgent):
  """
  A reflex agent that keeps its side Pacman-free. Again,
  this is to give you an idea of what a defensive agent
  could be like.  It is not the best or only way to make
  such an agent.
  """

  def getFeatures(self, gameState, action):
    features = util.Counter()
    successor = self.getSuccessor(gameState, action)
    DefCapsule = self.getCapsulesYouAreDefending(gameState)

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

    if action == Directions.STOP: features['stop'] = 1
    rev = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
    if action == rev: features['reverse'] = 1
    if len(DefCapsule) >0:
      features['DefCapsule'] = min([self.getMazeDistance(myPos, Cap) for Cap in DefCapsule])

    return features

  def getWeights(self, gameState, action):
    return {'numInvaders': -1000, 'onDefense': 100, 'invaderDistance': -10, 'stop': -100, 'reverse': -2, 'DefCapsule': -9}