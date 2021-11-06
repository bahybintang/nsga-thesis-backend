import csv
import os
import random
from population import Population
from box import Box
from individual import Individual


def generate_population(box_count, count):
    return [random.sample(list(range(1, box_count + 1)), box_count) for i in range(count)]


def loadData(boxData, gridX, gridY, gridZ, populationSize):
    # Read boxes data
    templateBoxes = []
    for box in boxData:
        box = [int(b) for b in box]
        templateBoxes.append(box)

    population_data = generate_population(len(templateBoxes), populationSize)

    # Read population data
    population = Population()
    for pop in population_data:
        pop = [int(p) for p in pop]
        boxes = []
        for p in pop:
            # If orientation not provided, randomize
            if len(templateBoxes[p - 1]) == 5:
                boxes.append(Box(*templateBoxes[p - 1], random.randint(0, 1)))
            # If orientation provided
            elif len(templateBoxes[p - 1]) == 6:
                boxes.append(Box(*templateBoxes[p - 1]))
            else:
                raise Exception("Invalid box data")
        population.append(Individual(boxes, gridX, gridY, gridZ))

    return population
