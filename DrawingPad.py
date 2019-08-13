from HexDecConverter import AHexDecConverter

import math

class ADrawingPad:
    '''
    A class that takes encoded hexadecimal-parameters
    and outputs commands for a drawing pad program.
    '''
    # Minimum and Maximum Color Values
    kMinMaxColorValues = (0, 255)

    # Minimum and Maximum Coordinate Point Values 
                                # ((x-min, x-max), (y-min, y-max))
    kMinMaxCoordinatePointValues = ((-8192, 8191), (-8192, 8191))

    # Opcode dictionary. 
    # Values are the translated command and number of byte args
    kCodebook = {
        "F0": ("CLR", 0),
        "80": ("PEN", 2),
        "A0": ("C0", 8),
        "C0": ("MV", 4)
    }

    # Minimum and Maximum decoded values from bytes
    kByteValueBounds = (-8192, 8191)

    def __init__(self):
        # I recognize that a lot of these also fall under the "Clear()" method,
        # but I put them here again for readability

        # Our byte encoder/decoder class from alpc1
        self.hexDecConverter = AHexDecConverter()

        self.currentPoint = (0, 0)      # Current pen coordinates
        self.lastPoint = (0, 0)         # last pen coordinates
        self.penUp = True               # If the pen is currently up or not
        self.outOfBounds = False        # If we're out of bounds
        self.penColor = (0, 0, 0, 255)  # The pen's current color

        # List of all commands since the program was started
        self.commandList = []           

        # List of commands from the last time Action() was run
        self.currentCommandList = []

    def Action(self, hexString):
        '''
        Parses hexString for opcodes, then translates the opcodes 
        and their arguments from encoded hexadecimal values to
        commands for a drawing pad program.

        Returns the stringified representation of the parsed commandList
        or an error message.
        '''
        hexStringLength = len(hexString)

        # If more than one char in hexString
        if hexStringLength > 1:
            # If an odd number of chars
            if hexStringLength % 2 > 0:
                hexString = hexString[:-1]
            # Split the list into bytecodes
            hexList = [
                hexString[i] + hexString[i+1] 
                for i in range(0, len(hexString), 2)
            ]
        else:
            return("Not enough arguments given.")

        # Resets Current Command List
        self.currentCommandList = []

        # Current Opcode
        currentCode = ""

        # While there are codes in hexList
        while len(hexList) > 0:
            # Args to send with our command
            hexArgs = []

            try:
                # Keep popping until we get a valid opcode
                while currentCode not in self.kCodebook:
                    currentCode = hexList.pop(0)
            except:
                pass # End of list

            # If our command is CLR, don't collect arguments
            if currentCode != "F0":
                try:
                    # Keep popping until there's another opcode in the queue
                    while hexList[0] not in self.kCodebook:
                        hexArgs.append(hexList.pop(0))
                except:
                    pass # End of list

            # Build Our Command Out
            self.__BuildCommand(currentCode, hexArgs)

            currentCode = ""

        # If at least one valid command was parsed
        if len(self.currentCommandList) > 0:
            # Add currentCommandList to commandList
            self.commandList += self.currentCommandList
        else:
            return "No valid commands were parsed"

        # Returns our command list
        return self.GetCommandString()

    def GetCommandString(self, current = True):
        '''
        Returns stringified commandList or 
        currentCommandList based on "current"
        '''
        # if current is True, send currentCommandList. Else send the full one.
        listToSend = self.currentCommandList if current else self.commandList

        return ";\n".join(listToSend) + ";"

    def __BuildCommand(self, command, hexArgs=[]):
        '''
        Sends command and args out to relevant method. 
        
        Returns True if successful.
        '''
        # If command is "CLR"
        if command == "F0":
            self.__Clear()

        # For all other commands
        else:
            # Decodes our args
            decodedArgs = self.__InterpretCodes(hexArgs)

            # Remove all invalid arguments
            decodedCommands = self.__RemoveInvalidCodes(command, decodedArgs)

            # If we had valid commands after all
            if decodedCommands != []:
                # If command is "PEN"
                if command == "80":
                    # Only grab the first (and only) argument
                    penCommand = decodedCommands[0]

                    self.__SetPenUp(penCommand)
                # If command is "C0"
                elif command == "A0":
                    # Convert colorCodes to a tuple
                    colorCodes = tuple(decodedCommands)

                    self.__SetColor(colorCodes)
                # If command is "MV"
                elif command == "C0":
                    numberOfCommands = len(decodedCommands)

                    # Re-organizes our arguments into coordinate pairs
                    coordinates = [
                        (decodedCommands[i], decodedCommands[i+1]) 
                        for i in range(0, numberOfCommands, 2)
                    ]

                    self.__MovePen(coordinates)

        return True

    def __Clear(self, sendToCommandList=True):
        '''
        Clears the current settings, making the current point (0,0), 
        setting the pen to the "up" position,setting outOfBounds to False, 
        and changing the color to (0,0,0,255) (black). 

        Also appends "CLR" to currentCommandList if sendToCommandList == True.
        '''
        self.currentPoint = (0, 0)      # Current pen coordinates
        self.lastPoint = (0, 0)         # last pen coordinates
        self.penUp = True               # If the pen is currently up or not
        self.outOfBounds = False        # If we're out of bounds
        self.penColor = (0, 0, 0, 255)  # The pen's current color

        # Sending "CLR" to the commandList is optional, but default
        if sendToCommandList:
            self.currentCommandList.append("CLR")

        return True

    def __SetPenUp(self, numCode):
        '''
        Sets penUp to True or False depending on numCode.

        Appends "PEN {UP/DOWN}" to currentCommandList depending on the code.
        '''
        currentPenUp = self.penUp

        # penUp is True if numCode was decoded as 0
        self.penUp = True if numCode == 0 else False

        # Don't add "PEN UP/DOWN" to command list if nothing has changed.
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
        minColor = self.kMinMaxColorValues[0]
        maxColor = self.kMinMaxColorValues[1]

        for colorCode in colorCodes:
            # If color code is not between our min and max values (0, 255)
            if not (minColor <= colorCode <= maxColor):
                return False

        # Sets the color
        self.penColor = colorCodes
        colorValueString = " ".join(str(i) for i in colorCodes)

        # Appends command to our list
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
        # Building our command
        currentCommand = "MV"

        # Set our last point to
        self.lastPoint = self.currentPoint

        # Iterates through all of our coordinate pairs
        for coordinatePair in coordinatePairsList:
            currentlyOutOfBounds = self.outOfBounds

            # Gets weighted coordinatePair
            weightedCoordinates = self.__WeighCoordinates(
                coordinatePair
            )

            # Sets currentPoint to the absolutePoint
            self.currentPoint = (coordinatePair[0] + self.currentPoint[0], 
              coordinatePair[1] + self.currentPoint[1])

            # If the weighted point differs from the absolute point
            if weightedCoordinates != self.currentPoint:
                self.outOfBounds = True
            else:
                self.outOfBounds = False

            # If going out of or coming back in bounds
            if self.outOfBounds != currentlyOutOfBounds:
                # If the pen isn't already up
                if not self.penUp:
                    # If now out of bounds
                    if self.outOfBounds:
                        # Append coordinates to our current command
                        currentCommand += " " + str(weightedCoordinates)

                        self.currentCommandList.append(currentCommand)
                        self.currentCommandList.append("PEN UP")
                    else:
                        # Coordinates upon re-entry
                        reEntryCoordinates = self.__WeighCoordinates(
                            self.lastPoint, False
                        )
                        # Append coordinates to our current command
                        currentCommand += " " + str(reEntryCoordinates)

                        self.currentCommandList.append(currentCommand)
                        self.currentCommandList.append("PEN DOWN")
                    
                    currentCommand = "MV"
            
            # If in bounds and the pen is down, 
            # append weighted coordinates to current command
            if not self.outOfBounds and not self.penUp:
                currentCommand += " " + str(weightedCoordinates)

            # Set last point to current point
            self.lastPoint = self.currentPoint

        # If the pen isn't down or we're out of bounds
        if self.penUp or self.outOfBounds:
            currentCommand += " " + str(weightedCoordinates)
            
        # If we have coordinates in it, add the command to command list
        if currentCommand != "MV":
            self.currentCommandList.append(currentCommand)

        return True

    def __WeighCoordinates(self, 
      unweightedCoordinates, testCurrentPoint=True):
        ''' 
        Modifies coordinates based on kMinMaxCoordinatePointValues
        and returns the result.
        '''
        minMaxValues = self.kMinMaxCoordinatePointValues

        # Absolute coordinates
        absoluteX = unweightedCoordinates[0] + self.currentPoint[0]
        absoluteY = unweightedCoordinates[1] + self.currentPoint[1]

        # Setting up our weighted coordinates
        weightedX = absoluteX
        weightedY = absoluteY
        weightedCoordinates = [weightedX, weightedY]

        # If we have a vertical or horizontal line between our coordinates
        if (absoluteX == self.currentPoint[0] or 
          absoluteY == self.currentPoint[1]):
            # If x is out of bounds in the negative direction
            if absoluteX < minMaxValues[0][0]:
                weightedCoordinates[0] = minMaxValues[0][0]
            # If x is out of bounds in the positive direction
            elif absoluteX > minMaxValues[0][1]:
                weightedCoordinates[0] = minMaxValues[0][1]
            # If y is out of bounds in the negative direction
            if absoluteY < minMaxValues[1][0]:
                weightedCoordinates[1] = minMaxValues[1][0]
            # If y is out of bounds in the positive direction
            elif absoluteY > minMaxValues[1][1]:
                weightedCoordinates[1] = minMaxValues[1][1]
        # If it's a diagonal line
        else:
            currentPoint = self.currentPoint

            unweightedX = unweightedCoordinates[0]
            unweightedY = unweightedCoordinates[1]

            weightedX = absoluteX
            weightedY = absoluteY

            try:
                # Get our tangent
                tangent = ((unweightedY) / (unweightedX))
            except: # Can't divide by 0
                tangent = 1

            # If x is out of bounds in the negative direction
            if absoluteX < minMaxValues[0][0]:
                weightedX = minMaxValues[0][0]
                if testCurrentPoint:
                    weightedY = math.ceil(currentPoint[0] + 
                    (minMaxValues[0][0] - currentPoint[0]) * tangent)
                else:
                    weightedY = math.ceil((minMaxValues[0][0] - 
                      currentPoint[0]) * tangent * 2)
            # If x is out of bounds in the positive direction
            elif absoluteX > minMaxValues[0][1]:
                weightedX = minMaxValues[0][1]
                if testCurrentPoint:
                    weightedY = math.ceil(currentPoint[0] + 
                    (minMaxValues[0][1] - currentPoint[0]) * tangent)
                else:
                    weightedY = math.ceil((minMaxValues[0][1] - 
                      currentPoint[0]) * tangent * 2)
            # If y is out of bounds in the negative direction
            elif absoluteY < minMaxValues[1][0]:
                weightedY = minMaxValues[1][0]
                
                try:
                    weightedX = math.ceil(currentPoint[1] + 
                      (minMaxValues[1][0] - currentPoint[1]) / tangent)
                except: # Can't divide by 0
                    weightedX = weightedX
            # If y is out of bounds in the positive direction
            elif absoluteY > minMaxValues[1][1]:
                weightedY = minMaxValues[1][1]
                
                try:
                    weightedX = math.ceil(currentPoint[1] + 
                      (minMaxValues[1][1] - currentPoint[1]) / tangent)
                except: # Can't divide by 0
                    weightedX = weightedX

            weightedCoordinates = [weightedX, weightedY]
        
        return tuple(weightedCoordinates)

    def __InterpretCodes(self, hexCodes):
        ''' 
        Interprets hexCodes and returns a list of decoded decimal numbers.
        '''
        numberOfCodes = len(hexCodes)

        # Will hold all of our decoded decimal arguments
        decodedCommands = []

        # If we have an odd number of codes
        if numberOfCodes % 2 > 0 and numberOfCodes > 0:
            hexCodes.pop()
            numberOfCodes = len(hexCodes)

        # If we have two or more codes
        if numberOfCodes > 0:
            # Get a list of decoded arguments using our pairs
            decodedCommands = [
                self.hexDecConverter.Decode(hexCodes[i], hexCodes[i+1]) 
                for i in range(0, numberOfCodes, 2) 
            ]
        
        return decodedCommands

    def __RemoveInvalidCodes(self, command, decimalArgs):
        ''' 
        Removes invalid codes from decimalArgs and returns the updated list.

        If the number of invalid codes is smaller than required for the 
        command, returns an empty list.
        '''
        # The number of hexadecimal arguments we need for each command
        numArgsRequired = int(self.kCodebook[command][1] / 2)
        argListLength = len(decimalArgs)

        # If command is "MV"
        if command == "C0":
            # For each decoded argument
            for i, dArg in enumerate(decimalArgs):
                # if out of our specified range of values (-8192, 8191)
                if not (self.kByteValueBounds[0] <= 
                  dArg <= self.kByteValueBounds[1]):
                    # Get a new list with only valid coordinate values
                    decimalArgs = decimalArgs[:i]
                    argListLength = len(decimalArgs)
                    break

            # Our coordinates must be in multiples of four
            argsTooMany = argListLength % numArgsRequired

            # Pop the last few codes if necessary to have our multiples of four
            for i in range(argsTooMany):
                decimalArgs.pop()

            # If we end up with fewer than 4 args altogether, empty the list
            if len(decimalArgs) < numArgsRequired:
                decimalArgs = []
        # For all other commands
        else:
            # We must have no more than the required number of arguments
            argsTooMany = argListLength - numArgsRequired
            # Pop any extra
            for i in range(argsTooMany):
                decimalArgs.pop()
            
            # Iterate through each argument
            for dArg in decimalArgs:
                # If any of them are outside of our decimal range
                if not (self.kByteValueBounds[0] <= 
                  int(dArg) <= self.kByteValueBounds[1]):
                    # Empty the list
                    decimalArgs = []
                    break

        return decimalArgs
    