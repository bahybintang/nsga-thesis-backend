class Box:
    def __init__(self, code, length,  width, height, weight, orientation):
        self.code = code
        self.length = length
        self.width = width
        self.height = height
        self.weight = weight
        self.orientation = orientation
        self.posX = None
        self.posY = None
        self.posZ = None

    def setPosition(self, posX, posY, posZ):
        self.posX = posX
        self.posY = posY
        self.posZ = posZ

    # getShape after orientation change
    def getShape(self):
        if self.orientation == 1:
            return self.width, self.length, self.height
        return self.length, self.width, self.height
