import math


class Individual:
    def __init__(self, boxes, gridX, gridY, gridZ):
        self.gridX = gridX
        self.gridY = gridY
        self.gridZ = gridZ
        self.boxes = boxes
        self.insertedBoxes = []
        self.maxHeight = 0
        self.rank = None
        self.crowdingDistance = None
        self.dominationCount = None
        self.dominatedSolutions = None
        self.objectives = {
            'weight': 0,
            'volume': 0,
            'center_of_mass': 0
        }
        self.fitness = 0

        # Position set
        self.positionSet = [(0, 0, 0)]

        for box in self.boxes:
            self.insertBox(box)

        self.calculateFitness()

    def isValidInsert(self, box, pos):
        # Initialize variable for non hanging area
        nonHangingArea = 0

        # Loop for each inserted box check if overlapping
        length, width, height = box.getShape()

        x1min = pos[0]
        x1max = x1min + length
        y1min = pos[1]
        y1max = y1min + width
        z1min = pos[2]
        z1max = z1min + height

        # Check if out of bin
        if x1max > self.gridX or y1max > self.gridY or z1max > self.gridZ:
            return False

        for bx in self.insertedBoxes:
            length, width, height = bx.getShape()
            x2min = bx.posX
            x2max = x2min + length
            y2min = bx.posY
            y2max = y2min + width
            z2min = bx.posZ
            z2max = z2min + height

            # Check if intersect
            if x1min + 0.5 < x2max and x2min < x1max - 0.5 and y1min + 0.5 < y2max and y2min < y1max - 0.5 and z1min + 0.5 < z2max and z2min < z1max - 0.5:
                return False

            # Get intersect area
            if z1min == z2max and x1min + 0.5 < x2max and x2min < x1max - 0.5 and y1min + 0.5 < y2max and y2min < y1max - 0.5:
                xImin = max(x1min, x2min)
                yImin = max(y1min, y2min)
                xImax = min(x1max, x2max)
                yImax = min(y1max, y2max)

                nonHangingArea += (xImax - xImin) * (yImax - yImin)

        return z1min == 0 or nonHangingArea == (x1max - x1min) * (y1max - y1min)

    def insertBox(self, box):
        # Get final box length, width, and height
        # consider orientation
        length, width, height = box.getShape()

        for i in range(len(self.positionSet)):
            if self.isValidInsert(box, self.positionSet[i]):
                box.setPosition(*self.positionSet[i])

                self.positionSet.pop(i)

                self.positionSet += [(box.posX + length, box.posY, box.posZ),
                                     (box.posX, box.posY + width, box.posZ),
                                     (box.posX, box.posY, box.posZ + height)]
                self.positionSet = sorted(
                    self.positionSet, key=lambda x: (x[2], x[1], x[0]))

                self.insertedBoxes.append(box)

                # Calculate max height for fitness calculation
                self.maxHeight = max(
                    self.maxHeight, box.posZ + height)

                return

    def calculateFitness(self):
        sumX = 0
        sumY = 0
        sumZ = 0
        sumWeight = 0
        for box in self.insertedBoxes:
            # Calculate fitness weight and volume
            length, width, height = box.getShape()
            self.objectives['weight'] += box.weight
            self.objectives['volume'] += length * width * height

            sumX += (box.posX + length / 2.0) * box.weight
            sumY += (box.posY + width / 2.0) * box.weight
            sumZ += (box.posZ + height / 2.0) * box.weight
            sumWeight += box.weight

        # Prevent division by 0
        sumWeight = 1 if sumWeight == 0 else sumWeight

        cx = sumX / sumWeight
        cy = sumY / sumWeight
        cz = sumZ / sumWeight
        self.objectives['center_of_mass'] = math.sqrt(
            ((self.gridX / 2.0) - cx)**2 + ((self.gridY / 2.0) - cy)**2 + ((self.maxHeight / 2.0) - cz)**2)

    def dominates(self, otherIndividual):
        orCondition = False
        andCondition = True

        orCondition = orCondition or self.objectives['volume'] > otherIndividual.objectives['volume']
        orCondition = orCondition or self.objectives['weight'] < otherIndividual.objectives['weight']
        orCondition = orCondition or self.objectives[
            'center_of_mass'] < otherIndividual.objectives['center_of_mass']

        andCondition = andCondition and self.objectives['volume'] >= otherIndividual.objectives['volume']
        andCondition = andCondition and self.objectives['weight'] <= otherIndividual.objectives['weight']
        andCondition = andCondition and self.objectives[
            'center_of_mass'] <= otherIndividual.objectives['center_of_mass']

        return orCondition and andCondition
