class Population:
    def __init__(self):
        self.individuals = []
        self.fronts = []

    def __len__(self):
        return len(self.individuals)

    def __iter__(self):
        return self.individuals.__iter__()

    def extend(self, newIndividuals):
        self.individuals.extend(newIndividuals)

    def append(self, newIndividual):
        self.individuals.append(newIndividual)
