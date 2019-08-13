from DrawingPad import ADrawingPad

drawingPad = ADrawingPad()

inFile = open("input.txt", "r")
outFile = open("output.txt", "w")

for line in inFile:
    outFile.write(drawingPad.Action(line))
    outFile.write("\n\n")

inFile.close()
outFile.close()