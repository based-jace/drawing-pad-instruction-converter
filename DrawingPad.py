from HexDecConverter import AHexDecConverter

import copy

#        1         2         3         4         5         6         7
# 34567890123456789012345678901234567890123456789012345678901234567890123456789

class ADrawingPad:
    '''
    A class that takes encoded hexadecimal-parameters
    and outputs commands for a drawing pad program.
    '''

    kMinMaxColorValues = (0, 255)
    kMinMaxCoordinatePointValues = ((-8192, 8191),(-8192, 8191))

    kCodebook = {
        "F0": ("CLR", 0),
        "80": ("PEN", 2),
        "A0": ("C0", 8),
        "C0": ("MV", 4)
    }

    kByteValueBounds = (-8192, 8191)

    def __init__(self):
        # I recognize that a lot of these also fall under the "Clear()" method,
        # but I put them here again for readability

        self.hexDecConverter = AHexDecConverter()

        self.currentPoint = (0, 0)
        self.lastValidPoint = (0, 0)
        self.penUp = True
        self.outOfBounds = False
        self.penColor = (0, 0, 0, 255)

        self.commandList = []
        self.currentCommandList = []

    def Action(self, hexString):
        '''
        Parses hexString for opcodes, then translates the opcodes 
        and their arguments from encoded hexadecimal values to
        commands for a drawing pad program.

        Returns the stringified representation of the parsed commandList
        '''

        hexList = [
            hexString[i] + hexString[i+1] 
            for i in range(0, len(hexString), 2)
        ]

        currentCode = ""
        while len(hexList) > 0:
            hexArgs = []
            currentCode = hexList.pop(0)
            while currentCode not in self.kCodebook:
                currentCode = hexList.pop(0)
            try:
                while hexList[0] not in self.kCodebook:
                    hexArgs.append(hexList.pop(0))
            except:
                # End of list
                pass
            
            self.__BuildCommand(currentCode, hexArgs)

        self.commandList += self.currentCommandList

        return self.GetCommandString()

    def GetCommandString(self, current = True):
        '''
        Returns stringified commandList or currentCommandList based on "current"
        '''

        listToSend = self.currentCommandList if current else self.commandList

        return ";\n".join(listToSend) + ";"

    def __BuildCommand(self, command, hexArgs=[]):
        '''
        Sends command and args out to relevant method. 
        
        Returns True if successful.
        '''

        if command == "F0":
            self.__Clear()
        else:
            decodedArgs = self.__InterpretCodes(hexArgs)
            decodedCommands = self.__RemoveInvalidCodes(command, decodedArgs)

            if decodedCommands != []:
        
                if command == "80":
                    penCommand = decodedCommands[0]

                    self.__SetPenUp(penCommand)

                elif command == "A0":
                    colorCodes = tuple(decodedCommands)
                    self.__SetColor(colorCodes)

                elif command == "C0":
                    numberOfCommands = len(decodedCommands)

                    coordinates = [
                        (decodedCommands[i], decodedCommands[i+1]) 
                        for i in range(0, numberOfCommands, 2)
                    ]

                    print(coordinates)

                    self.__MovePen(coordinates)

        return True

    def __Clear(self, sendToCommandList=True):
        '''
        Clears the current settings, making the current point (0,0), 
        setting the pen to the "up" position,setting outOfBounds to False, 
        and changing the color to (0,0,0,255) (black). 

        Also appends "CLR" to currentCommandList if sendToCommandList == True.
        '''

        self.currentPoint = (0, 0)
        self.lastValidPoint = (0, 0)
        self.penUp = True
        self.outOfBounds = False
        self.penColor = (0, 0, 0, 255)

        if sendToCommandList:
            self.currentCommandList.append("CLR")

        return True

    def __SetPenUp(self, numCode):
        '''
        Sets penUp to True or False depending on numCode.

        Appends "PEN {UP/DOWN}" to currentCommandList depending on the code.
        '''

        currentPenUp = self.penUp
        self.penUp = True if numCode == 0 else False

        if currentPenUp != self.penUp:
            upOrDown = "UP" if numCode == 0 else "DOWN"
            self.currentCommandList.append("PEN " + upOrDown)

        return True

    def __SetColor(self, colorCodes):
        '''
        Sets the current color based on the codes given. 

        Appends "C0 {r} {g} {b} {a}" to currentCommandList.

        Returns True if successful or False if a number
        is outside of our color range.
        '''

        for colorCode in colorCodes:
            if not (self.kMinMaxColorValues[0] <= 
              colorCode <= self.kMinMaxColorValues[1]):
                return False

        self.penColor = colorCodes
        colorValueString = " ".join(str(i) for i in colorCodes)

        self.currentCommandList.append("C0 " + colorValueString)

        return True

    def __MovePen(self, coordinatePairsList):
        ''' 
        Moves pen based on the coordinates decoded from the given hexArgs. 
        
        Appends "PEN {UP/DOWN}" to currentCommandList as necessary. 

        Also checks/sets outOfBounds and appends "MV ({x}, {y})" 
        to currentCommandList as necessary.

        Returns True if successful
        '''

        currentCommand = "MV"

        self.lastValidPoint = self.__CheckWeightedCoordinates(
            self.currentPoint
        )

        for coordinatePair in coordinatePairsList:
            currentlyOutOfBounds = self.outOfBounds
            unweightedX = coordinatePair[0] + self.currentPoint[0]
            unweightedY = coordinatePair[1] + self.currentPoint[1]
            unweightedCoordinates = (unweightedX, unweightedY)

            self.currentPoint = unweightedCoordinates

            weightedCoordinates = self.__CheckWeightedCoordinates(
                unweightedCoordinates
            )

            if weightedCoordinates != unweightedCoordinates:
                self.outOfBounds = True
            else:
                self.outOfBounds = False

            if self.outOfBounds != currentlyOutOfBounds:
                if not self.penUp:
                    if self.outOfBounds:
                        currentCommand += " " + str(weightedCoordinates)
                        self.currentCommandList.append(currentCommand)

                        self.currentCommandList.append("PEN UP")

                    else:
                        currentCommand += " " + str(self.lastValidPoint)
                        self.currentCommandList.append(currentCommand)

                        self.currentCommandList.append("PEN DOWN")
                    
                    currentCommand = "MV"

            if not self.outOfBounds and not self.penUp:
                currentCommand += " " + str(weightedCoordinates)

            self.lastValidPoint = weightedCoordinates

        if self.penUp or self.outOfBounds:
            currentCommand += " " + str(weightedCoordinates)
            
        if currentCommand != "MV":
            self.currentCommandList.append(currentCommand)

        return True

    def __CheckWeightedCoordinates(self, unweightedCoordinates):
        ''' 
        Modifies coordinates based on kMinMaxCoordinatePointValues
        and returns the result.
        '''

        minMaxValues = self.kMinMaxCoordinatePointValues

        unweightedX = unweightedCoordinates[0]
        unweightedY = unweightedCoordinates[1]

        weightedCoordinates = [unweightedX, unweightedY]

        if unweightedX < minMaxValues[0][0]:
            weightedCoordinates[0] = minMaxValues[0][0]
        elif unweightedX > minMaxValues[0][1]:
            weightedCoordinates[0] = minMaxValues[0][1]

        if unweightedY < minMaxValues[1][0]:
            weightedCoordinates[1] = minMaxValues[1][0]
        elif unweightedY > minMaxValues[1][1]:
            weightedCoordinates[1] = minMaxValues[1][1]

        weightedX = unweightedX - self.currentPoint[0]
        weightedY = unweightedY - self.currentPoint[1]
        print(weightedX,weightedY)
        print(weightedCoordinates)

        return tuple(weightedCoordinates)

    def __InterpretCodes(self, hexCodes):
        ''' 
        Interprets hexCodes and returns a list of decoded decimal numbers.
        '''

        numberOfCodes = len(hexCodes)

        decodedCommands = []

        if numberOfCodes % 2 > 0 and numberOfCodes > 0:
            hexCodes.pop()
            numberOfCodes = len(hexCodes)

        if numberOfCodes > 0:
            decodedCommands = [
                self.hexDecConverter.Decode(hexCodes[i], hexCodes[i+1]) 
                for i in range(0, numberOfCodes, 2)
            ]
        
        return decodedCommands

    def __RemoveInvalidCodes(self, command, decimalArgs):
        ''' 
        Removes invalid codes from decimalArgs and returns the updated list.

        If the number of invalid codes is smaller than required for the command,
        returns an empty list.
        '''

        numArgsRequired = int(self.kCodebook[command][1] / 2)
        argListLength = len(decimalArgs)

        if command == "C0":
            for i, dArg in enumerate(decimalArgs):
                if not (self.kByteValueBounds[0] <= dArg <= self.kByteValueBounds[1]):
                    decimalArgs = decimalArgs[:i]
                    argListLength = len(decimalArgs)
                    break

            argsTooMany = argListLength % numArgsRequired
            for i in range(argsTooMany):
                decimalArgs.pop()

            if len(decimalArgs) < numArgsRequired:
                decimalArgs = []

        else:
            argsTooMany = argListLength - numArgsRequired
            for i in range(argsTooMany):
                decimalArgs.pop()
            
            for dArg in decimalArgs:
                if not (self.kByteValueBounds[0] <= int(dArg) <= self.kByteValueBounds[1]):
                    decimalArgs = []
                    break

        return decimalArgs


dp = ADrawingPad()

# # Clear
# dp.BuildCommand("F0")

# # Pen Color
# dp.BuildCommand("A0", ["40","00","41","7F","40","00","41","7F"])

# # Move Pen
# dp.BuildCommand("C0", ["40","00","40","00"])

# # Pen Down
# dp.BuildCommand("80", ["40","01"])

# # Move
# dp.BuildCommand("C0", ["5F","20","5F","20"])

# # Pen Up
# dp.BuildCommand("80", ["40","00"])

# Green Line
# print(dp.Action("F0A04000417F4000417FC040004000804001C05F205F20804000"))

# Blue Square
# print(dp.Action("F0A040004000417F417FC04000400090400047684F5057384000804001C05F204000400001400140400040007E405B2C4000804000"))

# Red Lines
# print(dp.Action("F0A0417F40004000417FC067086708804001C0670840004000187818784000804000"))

# Orange Lines
print(dp.Action("F0A0417F41004000417FC067086708804001C067082C3C18782C3C804000"))