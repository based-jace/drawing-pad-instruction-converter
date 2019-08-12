from HexDecConverter import AHexDecConverter
import sys, copy

class ADrawingPad:
    ''' 
    Takes encoded hexadecimal data strings and converts commands into commands for a drawing pad program.
    '''

    # Minimum and Maximum possible color values
    kMinMaxColorValues = (0, 255)

    # Minimum and Maximum possible coordinate values
    kMinMaxCoordinateValues = (-8192, 8191)

    # A dictionary of codes and their corresponding ["DrawingPad Command", numberOfByteCodesPerArgument]
    # NOTE: The number of byte codes for "MV" is -1, because it can be any number of pairs (any multiple of 4 codes)
    kCodeBook = {
        "F0": ["CLR", 0], 
        "80": ["PEN", 2],
        "A0": ["C0", 8], 
        "C0": ["MV", -1]
    }

    # For Accessing Codes from the codebook manually
    kPlainEnglishCodes = {
        "CLEAR": "F0",
        "PEN": "80",
        "COLOR": "A0",
        "MOVE": "C0"
    }

    def __init__(self):
        # Utilizes the HexDecConverter from the first test
        self.hexDecConverter = AHexDecConverter()

        # All commands performed since starting program
        self.commandsPerformed = ""

        # Current command being created
        self. currentCommand = ""

        # Last set of commands performed
        self.lastCommandSet = []

        self.Clear(False)
        
    def Clear(self, addCommandToList=True):
        ''' 
        Sets the pen color to black, sets the pen position to origin, and raises the pen 
        '''

        self.penColor = (0, 0, 0, 255)  # Color: Black
        self.penPosition = (0, 0)       # Point: Origin
        self.penUp = True               # Pen:   Raised
        self.outOfBounds = False        # Overwrites whether pen is raised
        if addCommandToList:
            self.AddAndResetCurrentCommand(self.GetCodePlainEnglish("CLEAR")[0])

    def Action(self, hexString):
        ''' 
        Main method - takes a string representing encoded instruction, and returns decoded drawing commands 
        '''

        self.EnsureCommandString(hexString)
        return self.GetDrawingCommandList(hexString)

    def EnsureCommandString(self, hexString):
        ''' 
        Tests that a hex string is even and is valid hexadecimal 
        '''

        try:
            int(hexString, 16)
            if len(str(hexString)) % 2 != 0:
                raise ValueError("ValueError: Hex String has an odd number of characters")
        except Exception as error:
            print(error)
            return False
        return True

    def GetDrawingCommandList(self, hexString):
        ''' 
        Returns a string made up of formatted drawing commands 
        '''

        # Splits the hexString into a list of two-character strings
        hexList = [hexString[i:i+2] for i in range(0, len(hexString), 2)]

        # Caches to keep track of pontential routes
        hexCache, commandCache, penUpCache = [], [], []
        coordList = []
        self.lastCommandSet = []
        hexcode = hexList.pop(0)
        hexPair = self.kCodeBook[hexcode]
        print(hexList)
        while len(hexList) > 0:
            try:
                if hexcode == "":
                    hexcode = hexList.pop(0)
                    if self.TestCodeBook(hexcode):
                        hexPair = self.kCodeBook[hexcode]
                    else:
                        raise ValueError("ValueError: Command not found")

                if hexPair[1] == -1:
                    xCoord = "".join([hexList.pop(0) for i in range(2)])
                    yCoord = "".join([hexList.pop(0) for i in range(2)])
                    coordList.append([xCoord, yCoord])
                    if len(hexList) > 0 and hexList[0] in self.kCodeBook:
                        (self.BuildCommand(hexPair[0], coordList))
                        hexCache.append(hexList)
                        commandCache.append(self.lastCommandSet)
                        penUpCache.append(self.penUp)
                        hexcode = hexList.pop(0)
                        hexPair = self.kCodeBook[hexcode]
                else:
                    commandArgs = ["".join([hexList.pop(0), hexList.pop(0)]) for i in range(0, hexPair[1], 2)]
                    self.BuildCommand(hexPair[0], commandArgs)
                    hexcode = ""
            except: 
                hexList = hexCache.pop()
                self.lastCommandSet = commandCache.pop()
                hexPair = self.kCodeBook[hexList.pop(0)]
                self.penUp = penUpCache.pop()
        # print(self.lastCommandSet)
        commandString = ";\n".join(self.lastCommandSet) + ";"
        self.commandsPerformed += "\n" + commandString
        return commandString

    def TestCodeBook(self, command):
        if command in self.kCodeBook:
            return True
        return False

    def BuildCommand(self, command, hexArgs):
        '''
        Creates command output from given commandPair and encoded arguments
        '''

        # Clear DrawingPad
        if command == "CLR":
            self.Clear()

        # Move Pen
        elif command == "MV":
            decodedCoordinates = [
                [
                    self.hexDecConverter.Decode(coordPair[0][:2], coordPair[0][2:]),
                    self.hexDecConverter.Decode(coordPair[1][:2], coordPair[1][2:])
                ]
                for coordPair in hexArgs
            ]
            self.MovePen(decodedCoordinates)

        # Raise/Lower Pen
        elif command == "PEN":
            hi, lo = hexArgs[0][:2], hexArgs[0][2:]
            # print(hi, lo)
            upOrDownCode = self.hexDecConverter.Decode(hi, lo)
            if not self.outOfBounds:
                if int(upOrDownCode) == 0:
                    self.SetPenUp(True)
                    command += " UP"
                else:
                    self.SetPenUp(False)
                    command += " DOWN"
                self.AddAndResetCurrentCommand(command)

        # Set Pen Color
        elif command == "C0":
            commandArgs = [str(self.hexDecConverter.Decode(arg[:2], arg[2:])) for arg in hexArgs]
            for arg, i in enumerate(hexArgs):
                numArg = int(arg)
                if numArg > self.kMinMaxColorValues[1]:
                    hexArgs[i] = self.kMinMaxColorValues[1]
                elif numArg < self.kMinMaxColorValues[0]:
                    hexArgs[i] = self.kMinMaxColorValues[0]

            command += " " + " ".join(commandArgs)
            self.AddAndResetCurrentCommand(command)

        return True

    def CheckIfOutOfBounds(self, coordinateSet):
        '''
        Checks if coordinates are out of bounds, and returns coordinates within boundaries 
        '''
        for i, coordinate in enumerate(coordinateSet):
            coordNum = int(coordinate)
            currentlyOutOfBounds = self.outOfBounds

            if coordNum > self.kMinMaxCoordinateValues[1]:
                coordinateSet[i] = self.kMinMaxCoordinateValues[1]
                currentlyOutOfBounds = True
            elif coordNum < self.kMinMaxColorValues[0]:
                coordinateSet[i] = self.kMinMaxCoordinateValues[0]
                currentlyOutOfBounds = True
            else:
                currentlyOutOfBounds = False

        if self.outOfBounds != currentlyOutOfBounds:
            if self.outOfBounds:
                self.AddAndResetCurrentCommand("PEN UP")
            else:
                self.AddAndResetCurrentCommand("PEN DOWN")

        return coordinateSet

    def MovePen(self, coordinates):
        ''' 
        Moves the pen based on the coordinates given 
        '''

        coordString = ""
        for relCoords in coordinates:
            tempCoords = [relCoords[i] + self.penPosition[i] for i in range(2)]

            coords = tuple(self.CheckIfOutOfBounds(tempCoords))

            if (not self.penUp or self.outOfBounds) and tempCoords != self.penPosition:
                coordString = " (" + str(coords[0]) + ", " + str(coords[1]) + ")"
                if "MV" in self.currentCommand:
                    print(self.outOfBounds, self.penUp, coordString, tempCoords)
                    self.currentCommand += (coordString)
                else:
                    self.currentCommand = ("MV" + coordString)

            self.penPosition = tuple(tempCoords)

        if self.penUp:
            if self.CheckIfMoving():
                self.currentCommand += (" (" + str(coords[0]) + ", " + str(coords[1]) + ")")
            else:
                self.AddAndResetCurrentCommand("MV" + coordString)
        self.AddAndResetCurrentCommand()
        return True

    def CheckIfMoving(self):
        '''
        Returns True if "MV" is in currentCommand
        '''
        if "MV" in self.currentCommand:
            return True
        return False

    def SetPenUp(self, penUp):
        ''' 
        Sets whether the pen is up or down based on passed in boolean variable (penUp) 
        '''
        self.penUp = penUp
        return True

    def AddAndResetCurrentCommand(self, command=""):
        ''' 
        Adds current command to lastCommandSet and resets current command to "" 
        '''
        self.AddToCurrentCommand(command)
        if self.currentCommand != "":
            self.lastCommandSet.append(self.currentCommand)
            self.currentCommand = ""
        return True
    
    def AddToCurrentCommand(self, string):
        ''' 
        Adds given string to current command 
        '''
        self.currentCommand += string
        return True

    def AddToCommandList(self, command):
        ''' 
        Adds given command to lastCommandSet 
        '''
        self.lastCommandSet += command
        return True

    def UpdateCommandList(self, command):
        ''' 
        Adds lastCommandSet to commandsPerformed 
        '''
        self.commandsPerformed += "\n" + self.lastCommandSet
        return True

    def GetCodePlainEnglish(self, plainEnglishCode):
        ''' 
        Returns drawing pad command and number of bytes using the given plainEnglishCode 
        '''
        print(type(self.kPlainEnglishCodes[plainEnglishCode]))
        return self.kCodeBook[self.kPlainEnglishCodes[plainEnglishCode.upper()]]

dp = ADrawingPad()
test = dp.Action("F0A0417F40004000417FC067086708804001C0670840004000187818784000804000")

print(test)