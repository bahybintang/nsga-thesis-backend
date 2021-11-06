import random
import os
from tqdm import tqdm
from population import Population
from individual import Individual
from box import Box
from flask_socketio import SocketIO


class GeneticAlgorithm:
    def __init__(self, population, mutationProbability, maxGeneration, room_id):
        self.mutationProbability = mutationProbability
        self.population = population
        self.maxGeneration = maxGeneration
        self.individualCount = len(population)
        self.finalPopulation = None
        self.room_id = room_id
        self.socket = SocketIO(message_queue=os.getenv(
            'REDIS_URL'), cors_allowed_origins=os.getenv('CLIENT_ORIGIN'))

    def start(self):
        self.fastNonDominatedSort(self.population)
        for front in self.population.fronts:
            self.calculateCrowdingDistance(front)
        children = self.createChildren(self.population)

        # Save current population and advance to next generation
        self.finalPopulation = self.population

        with tqdm(total=self.maxGeneration, desc="Generation") as t:
            for _ in range(self.maxGeneration):
                self.population.extend(children)
                self.fastNonDominatedSort(self.population)
                newPopulation = Population()
                frontNum = 0

                # Remove individuals that exceed max indvidualCount
                # sorted by rank and crowding distance
                while len(newPopulation) + len(self.population.fronts[frontNum]) <= self.individualCount:
                    self.calculateCrowdingDistance(
                        self.population.fronts[frontNum])
                    newPopulation.extend(self.population.fronts[frontNum])
                    frontNum += 1

                self.calculateCrowdingDistance(
                    self.population.fronts[frontNum])
                self.population.fronts[frontNum].sort(
                    key=lambda individual: individual.crowdingDistance, reverse=True)
                newPopulation.extend(
                    self.population.fronts[frontNum][0:self.individualCount - len(newPopulation)])

                self.population = newPopulation

                self.fastNonDominatedSort(self.population)
                for front in self.population.fronts:
                    self.calculateCrowdingDistance(front)
                children = self.createChildren(self.population)

                # Save current population and advance to next generation
                self.finalPopulation = self.population

                t.update()
                self.socket.emit(
                    'ga-progress', t.format_dict, room=self.room_id)

    def fastNonDominatedSort(self, population):
        population.fronts = [[]]
        for individual in population:
            individual.dominationCount = 0
            individual.dominatedSolutions = []
            for otherIndividual in population:
                if individual.dominates(otherIndividual):
                    individual.dominatedSolutions.append(otherIndividual)
                elif otherIndividual.dominates(individual):
                    individual.dominationCount += 1
            if individual.dominationCount == 0:
                individual.rank = 0
                population.fronts[0].append(individual)
        i = 0
        while len(population.fronts[i]) > 0:
            temp = []
            for individual in population.fronts[i]:
                for otherIndividual in individual.dominatedSolutions:
                    otherIndividual.dominationCount -= 1
                    if otherIndividual.dominationCount == 0:
                        otherIndividual.rank = i + 1
                        temp.append(otherIndividual)
            i = i + 1
            population.fronts.append(temp)

    def calculateCrowdingDistance(self, front):
        if len(front) > 0:
            individualCount = len(front)

            # Set default crowdingDistance to 0
            for individual in front:
                individual.crowdingDistance = 0

            # Loop through objectives
            for key in front[0].objectives:
                front.sort(key=lambda individual: individual.objectives[key])

                # Set individual with the maximum and minimum objectives value
                # to really big number, so it always chosen first
                front[0].crowdingDistance = 10**5
                front[individualCount - 1].crowdingDistance = 10**5
                mValues = [individual.objectives[key] for individual in front]

                # Calculate scale to normalize
                scale = max(mValues) - min(mValues)

                # Avoid divide by 0
                scale = scale if scale != 0 else 1

                # Calculate crowdingDistance for other individuals
                for i in range(1, individualCount - 1):
                    front[i].crowdingDistance += (
                        front[i + 1].objectives[key] - front[i - 1].objectives[key]) / scale

    def createChildren(self, population):
        children = []
        while len(children) < len(population):
            parent1 = self.__tournament(population)
            parent2 = parent1
            while parent1 == parent2:
                parent2 = self.__tournament(population)
            child = self.__crossover(parent1, parent2)
            if random.random() < self.mutationProbability:
                self.__mutate(child, parent1)
            children.append(Individual(child, parent1.gridX,
                                       parent1.gridY, parent1.gridZ))

        return children

    def __mutate(self, child, std):
        rng = random.random()

        # Swap packing order
        if rng < 0.5:
            pos1 = random.randint(0, len(child) - 1)
            pos2 = random.randint(0, len(child) - 1)
            tmp = child[pos1]
            child[pos1] = child[pos2]
            child[pos2] = tmp
        # Flip orientation
        else:
            pos = random.randint(0, len(child) - 1)
            child[pos].orientation = (child[pos].orientation + 1) % 2

        return child

    def __crossover(self, ind1, ind2):
        # Deep copy box
        parent1 = [Box(box.code, box.length, box.width, box.height,
                       box.weight, box.orientation) for box in ind1.boxes]
        parent2 = [Box(box.code, box.length, box.width, box.height,
                       box.weight, box.orientation) for box in ind2.boxes]

        # PMX crossover
        pos1 = [0] * (len(parent1) + 1)
        pos2 = [0] * (len(parent2) + 1)
        done = [False] * (len(parent1) + 1)

        for i in range(len(parent1)):
            pos1[parent1[i].code] = i

        for i in range(len(parent2)):
            pos2[parent2[i].code] = i

        # Choose crossover points
        cxpoint1 = random.randint(0, len(parent1))
        cxpoint2 = random.randint(0, len(parent1) - 1)
        if cxpoint2 >= cxpoint1:
            cxpoint2 += 1
        else:  # Swap the two cx points
            cxpoint1, cxpoint2 = cxpoint2, cxpoint1

        children = [None] * len(parent1)
        for i in range(cxpoint1, cxpoint2):
            children[i] = parent1[i]
            done[parent1[i].code] = True

        for i in range(cxpoint1, cxpoint2):
            if not done[parent2[i].code]:
                found_pos = pos2[parent1[i].code]
                while children[found_pos] != None:
                    found_pos = pos2[parent1[found_pos].code]
                children[found_pos] = parent2[i]
                done[parent2[i].code] = True

        j = 0
        for i in range(len(parent2)):
            if not done[parent2[i].code]:
                while children[j] != None:
                    j += 1
                children[j] = parent2[i]
                done[parent2[i].code] = True

        return children

    def __tournament(self, population):
        selectedIndividuals = random.sample(population.individuals, 2)
        if selectedIndividuals[0].rank < selectedIndividuals[1].rank:
            return selectedIndividuals[0]
        elif selectedIndividuals[0].rank == selectedIndividuals[1].rank and selectedIndividuals[0].crowdingDistance > selectedIndividuals[1].crowdingDistance:
            return selectedIndividuals[0]
        else:
            return selectedIndividuals[1]
