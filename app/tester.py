import random
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib as mpl
import csv
import os
import plotly
import plotly.graph_objects as go
import json
from tabulate import tabulate
from scipy import stats
from mpl_toolkits.mplot3d import Axes3D

mpl.rcParams['figure.dpi'] = 200
color_hash_map = ["#%06x" % random.randint(0, 0xFFFFFF) for i in range(500)]


def showGraphPlotly(individual, show=True):
    data = []

    for box in individual.insertedBoxes:
        length, width, height = box.getShape()
        data.append(go.Mesh3d(
            x=[box.posX, box.posX, box.posX + length, box.posX + length,
                box.posX, box.posX, box.posX + length, box.posX + length],
            y=[box.posY, box.posY + width, box.posY + width, box.posY,
                box.posY, box.posY + width, box.posY + width, box.posY],
            z=[box.posZ, box.posZ, box.posZ, box.posZ, box.posZ + height,
                box.posZ + height, box.posZ + height, box.posZ + height],
            color=color_hash_map[box.code],
            i=[7, 0, 0, 0, 4, 4, 6, 6, 4, 0, 3, 2],
            j=[3, 4, 1, 2, 5, 6, 5, 2, 0, 1, 6, 3],
            k=[0, 7, 2, 3, 6, 7, 1, 1, 5, 5, 7, 6],
            showscale=True,
            name='Box ' + str(box.code) + '  pos' + str((box.posX,
                                                         box.posY, box.posZ)) + ' size' + str(box.getShape())
        ))
        data.append(go.Scatter3d(
            x=[box.posX + length / 2],
            y=[box.posY + width / 2],
            z=[box.posZ + height / 2],
            mode="markers",
            marker=dict(
                size=5,
                color=color_hash_map[box.code]
            ),
            name='Box ' + str(box.code) + '  pos' + str((box.posX,
                                                         box.posY, box.posZ)) + ' size' + str(box.getShape())
        ))

    fig = go.Figure(data)
    fig.add_annotation(
        text=f"Inserted boxes: {len(individual.insertedBoxes)}", xref="paper", yref="paper", x=0, y=1, showarrow=False)
    fig.add_annotation(
        text=f"Center of mass: {individual.objectives['center_of_mass']}", xref="paper", yref="paper", x=0, y=1.1, showarrow=False)
    fig.add_annotation(
        text=f"Volume: {individual.objectives['volume']}", xref="paper", yref="paper", x=0, y=1.2, showarrow=False)
    fig.add_annotation(
        text=f"Weight: {individual.objectives['weight']}", xref="paper", yref="paper", x=0, y=1.3, showarrow=False)

    mins = min(individual.gridX, individual.gridY, individual.gridZ)

    fig.update_layout(
        scene=dict(
            xaxis=dict(nticks=4, range=[0, individual.gridX]),
            yaxis=dict(nticks=4, range=[0, individual.gridY]),
            zaxis=dict(nticks=4, range=[0, individual.gridZ])
        ),
        scene_aspectmode='manual',
        scene_aspectratio=dict(
            x=individual.gridX/mins, y=individual.gridY/mins, z=individual.gridZ/mins)
    )

    if show:
        fig.show()

    return fig


class Tester:
    def __init__(self, GA, show=True, save=False, savePath=None, room_id=""):
        self.finalPopulation = GA.finalPopulation
        self.savePath = savePath
        self.save = save
        self.show = show
        self.room_id = room_id

        if save and self.savePath is not None:
            os.system("mkdir -p {}".format(savePath))

        assert not(
            save and savePath is None), "savePath must be provided if save=True"

    def savePopulation(self):
        population = self.finalPopulation
        individuals = self.getRankedIndividuals(population.individuals)
        data = []
        for i in individuals:
            data.append([i.fitness, i.objectives['center_of_mass'],
                         i.objectives['volume'], i.objectives['weight']])
            data.append([b.code for b in i.boxes] +
                        [b.orientation for b in i.boxes])

        f = open(os.path.join(self.savePath,
                              'population_{}.csv'.format("final")), 'w')
        csv.writer(f).writerows(data)

    def getObjectiveDevelopment(self):
        weights = []
        centerOfMasses = []
        volumes = []

        for p in self.populationHistory:
            rankedIndividuals = self.getRankedIndividuals(p.fronts[0])
            weights.append(rankedIndividuals[0].objectives['weight'])
            centerOfMasses.append(
                rankedIndividuals[0].objectives['center_of_mass'])
            volumes.append(rankedIndividuals[0].objectives['volume'])

        fig = plt.figure()
        plt.plot(weights, label='objective development')
        plt.title('Weight Objective Development on Best Individual')
        plt.ylabel('Objective Value')
        plt.xlabel("Generation")
        plt.legend(loc='best')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     "development_weight.jpg"), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        fig = plt.figure()
        plt.plot(centerOfMasses, label='objective development')
        plt.title('Center of Mass Objective Development on Best Individual')
        plt.ylabel('Objective Value')
        plt.xlabel("Generation")
        plt.legend(loc='best')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     "development_centerofmass.jpg"), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        fig = plt.figure()
        plt.plot(volumes, label='objective development')
        plt.title('Volume Objective Development on Best Individual')
        plt.ylabel('Objective Value')
        plt.xlabel("Generation")
        plt.legend(loc='best')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     "development_volume.jpg"), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

    def getSpearmanRankCorrelation(self):
        keys = [
            key for key in self.finalPopulation.individuals[0].objectives]

        objectives = [[i.objectives[key] for i in self.finalPopulation.fronts[0]]
                      for key in keys]

        correlation = [[stats.spearmanr(o1, o2).correlation
                        for o2 in objectives] for o1 in objectives]

        pvalue = [[stats.spearmanr(o1, o2).pvalue
                   for o2 in objectives] for o1 in objectives]

        # Add table header
        correlation = [[keys[i]] + c for i, c in enumerate(correlation)]
        pvalue = [[keys[i]] + p for i, p in enumerate(pvalue)]
        correlation = [keys] + correlation
        pvalue = [keys] + pvalue

        if self.save:
            fCor = open(os.path.join(self.savePath,
                                     "correlation_{}.csv".format("final")), "w")
            csv.writer(fCor).writerows(correlation)
            fPval = open(os.path.join(
                self.savePath, "pvalue_{}.csv".format("final")), "w")
            csv.writer(fPval).writerows(pvalue)

        if self.show:
            print("Correlation")
            print(tabulate(correlation, headers='firstrow'))

            print("\nPValue")
            print(tabulate(pvalue, headers='firstrow'))

    def getRankedIndividuals(self, individuals, comparator, reverse=True):
        volumes = [i.objectives['volume']
                   for i in individuals]
        maxVol, minVol = max(volumes), min(volumes)
        scaleVol = maxVol - minVol
        if scaleVol == 0:
            scaleVol = 1

        weights = [i.objectives['weight']
                   for i in individuals]
        maxWei, minWei = max(weights), min(weights)
        scaleWei = maxWei - minWei
        if scaleWei == 0:
            scaleWei = 1

        centerOfMass = [i.objectives['center_of_mass']
                        for i in individuals]
        maxMass, minMass = max(centerOfMass), min(centerOfMass)
        scaleMass = maxMass - minMass
        if scaleMass == 0:
            scaleMass = 1

        for i in individuals:
            i.fitness = 0

            # Minimize
            i.fitness += 1 - \
                (i.objectives['center_of_mass'] - minMass) / scaleMass

            # Maximize
            i.fitness += (i.objectives['weight'] - minWei) / scaleWei
            i.fitness += (i.objectives['volume'] - minVol) / scaleVol

        return sorted(individuals, key=comparator, reverse=reverse)

    def getBestIndividual(self, comp_type="fitness"):
        if comp_type == "fitness":
            def comparator(x): return x.fitness
        elif comp_type == "center_of_mass":
            def comparator(x): return x.objectives["center_of_mass"]
        elif comp_type == "volume":
            def comparator(x): return x.objectives["volume"]
        elif comp_type == "weight":
            def comparator(x): return x.objectives["weight"]

        rankedIndividuals = self.getRankedIndividuals(
            self.finalPopulation.fronts[0], comparator, reverse=False if comp_type == "center_of_mass" else True)

        fig = showGraphPlotly(rankedIndividuals[0], show=self.show)

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        return graphJSON

    def getObjectiveGraph(self):
        volumes = [i.objectives['volume']
                   for i in self.finalPopulation.fronts[0]]
        weights = [i.objectives['weight']
                   for i in self.finalPopulation.fronts[0]]
        centerOfMass = [i.objectives['center_of_mass']
                        for i in self.finalPopulation.fronts[0]]

        vol = [i.objectives['volume']
               for i in self.finalPopulation.fronts[0]]
        com = [i.objectives['center_of_mass']
               for i in self.finalPopulation.fronts[0]]
        wei = [i.objectives['weight']
               for i in self.finalPopulation.fronts[0]]

        fig = plt.figure()
        ax = fig.add_subplot(111, projection='3d')
        ax.scatter(vol, com, wei, c=wei, cmap='viridis')
        ax.set_xlabel('Volume')
        ax.set_ylabel('Center of Mass')
        ax.set_zlabel('Weight')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'scatter_all_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        # CENTER OF MASS & VOLUME
        fig = plt.figure()
        plt.title('Center of Mass & Volume Scatter Plot')
        plt.scatter(vol, com, c=com, cmap='viridis')
        plt.xlabel('Volume')
        plt.ylabel('Center of Mass')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'scatter_volume_centerofmass_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        # VOLUME & WEIGHT
        fig = plt.figure()
        plt.title('Volume & Weight Scatter Plot')
        plt.scatter(vol, wei, c=wei, cmap='viridis')
        plt.xlabel('Volume')
        plt.ylabel('Weight')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'scatter_volume_weight_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        # CENTER OF MASS & WEIGHT
        fig = plt.figure()
        plt.title('Center of Mass & Weight Scatter Plot')
        plt.scatter(com, wei, c=wei, cmap='viridis')
        plt.xlabel('Center of Mass')
        plt.ylabel('Weight')
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'scatter_centerofmass_weight_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        # Box Plot Volume
        fig = plt.figure()
        plt.title('Volume')
        plt.boxplot(volumes)
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'boxplot_volume_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        # Box Plot Weight
        fig = plt.figure()
        plt.title('Weight')
        plt.boxplot(weights)
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'boxplot_weight_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()

        # Box Plot Center of Mass
        fig = plt.figure()
        plt.title('Center of Mass')
        plt.boxplot(centerOfMass)
        if self.save:
            fig.savefig(os.path.join(self.savePath,
                                     'boxplot_centerofmass_{}.jpg'.format("final")), bbox_inches="tight")
        if self.show:
            plt.show()
        plt.close()
