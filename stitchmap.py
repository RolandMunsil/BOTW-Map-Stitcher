from PIL import Image
from os import listdir
from os import path
from functools import reduce
from argparse import ArgumentParser


ALL_REGIONS_VISIBLE = 0b111111111111111 #15 bits
ALL_MODIFICATIONS_TRIGGERED = 0b111111 #6 bits
NUM_COLUMNS = 12
NUM_ROWS = 10
ELDIN_BRIDGE_VISIBILITY_BIT = 0b000001000000000
TARREY_TOWN_VISIBILITY_BIT =  0b000010000000000

regionsVisibleBitmasks = None
modificationsTriggeredBitmasks = None

def getTileInfo(filename):
    #remove extension
    filename = filename.split('.')[0]
    underscoreparts = filename.split('_')
    loc = underscoreparts[1][0:3]
    col = ord(loc[0]) - ord('A')
    row = int(loc[2])

    tileRegionsVisibleFlags = None
    tileModificationsTriggeredFlags = None
    if(len(underscoreparts) > 2):
        flagparts = underscoreparts[2].split('-')
        if(len(flagparts) > 1):
            tileRegionsVisibleFlags = int(flagparts[0])
            tileModificationsTriggeredFlags = int(flagparts[1])
        else:
            tileRegionsVisibleFlags = int(underscoreparts[2])
            tileModificationsTriggeredFlags = 0
    else:
        if(regionsVisibleBitmasks == None):
            tileRegionsVisibleFlags = None
        else:
            tileRegionsVisibleFlags = regionsVisibleBitmasks[col][row]

        possibleModsTriggeredFlags = underscoreparts[1][4:]
        if(possibleModsTriggeredFlags != "" and possibleModsTriggeredFlags != None):
            tileModificationsTriggeredFlags = int(possibleModsTriggeredFlags)
        else:
            tileModificationsTriggeredFlags = 0

    return (col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags)

#
#
# Code used to generate the flagmasks.txt file
# In short, it figures out bitmasks from the variations of tiles with variations,
# and to figure out the rest it uses a basic fill algorithm (since the tiles with
# variations are essentially "edges"
#
#
#def getOrReturnNone(bitmasks, col, row) -> int:
#    if(col < 0 or row < 0 or col >= NUM_COLUMNS or row >= NUM_ROWS):
#        return None
#    else:
#        return bitmasks[col][row]

#def hasSingleFlag(bm) -> bool:
#    return bm != 0 and ((bm & (bm - 1)) == 0)

#def calculateRegionsVisibileBitmasks(folderpath):
#    bitmasks = make2DDict(None)
#    for filename in listdir(folderpath):
#        if(filename.endswith(".png")):
#            col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags = getTileInfo(filename)
#            if(tileRegionsVisibleFlags == None):
#                continue
#            if(bitmasks[col][row] == None):
#                bitmasks[col][row] = 0
#            bitmasks[col][row] |= int(tileRegionsVisibleFlags)
    
#    nonesStillExist = True
#    while(nonesStillExist):
#        nonesStillExist = False
#        for col in range(0, NUM_COLUMNS):
#            for row in range(0, NUM_ROWS):
#                if(bitmasks[col][row] == None):
#                    nonesStillExist = True
#                    # get masks for surrounding tiles
#                    surroundingMasks = [getOrReturnNone(bitmasks, c, r) for c in range(col-1,col+2) for r in range(row-1,row+2)]
#                    # remove nones
#                    surroundingMasksFiltered = list(filter(None, surroundingMasks))
#                    if(len(surroundingMasksFiltered) > 0):
#                        #try to find common single bit
#                        commonBits = reduce(lambda b1, b2: b1 & b2, surroundingMasksFiltered)
#                        if(hasSingleFlag(commonBits)):
#                            bitmasks[col][row] = commonBits

#    return bitmasks

#def calculateModificationsTriggeredBitmasks(folderpath):
#    bitmasks = make2DDict(initialValue=0)

#    for filename in listdir(folderpath):
#        if(filename.endswith(".png")):
#            col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags = getTileInfo(filename)
#            bitmasks[col][row] |= tileModificationsTriggeredFlags
#    return bitmasks

#def generateBitmasksFile():
#    regionsVisibleBitmasks = getRegionsVisibileBitmasks(fullpath)
#    modificationsTriggeredBitmasks = getModificationsTriggeredBitmasks(fullpath)

#    flagmasksfile = open("flagmasks.txt","w+")
#    for col in range(0, NUM_COLUMNS):
#        for row in range(0, NUM_ROWS):
#            c = chr(ord('A') + col)
#            r = "{:0>15b}".format(regionsVisibleBitmasks[col][row])
#            e = "{:0>6b}".format(modificationsTriggeredBitmasks[col][row])
#            flagmasksfile.write(f"{c}-{row} {r} {e}\n")
#    flagmasksfile.close()

def make2DDict(initialValue = None):
    tiles = {}
    for col in range(0, NUM_COLUMNS):
        tiles[col] = {}
        for row in range(0, NUM_ROWS):
            tiles[col][row] = initialValue
    return tiles

def loadBitmasks():
    global regionsVisibleBitmasks
    global modificationsTriggeredBitmasks
    regionsVisibleBitmasks = make2DDict(initialValue=0)
    modificationsTriggeredBitmasks = make2DDict(initialValue=0)

    flagmasksfile = open("flagmasks.txt","r")
    for line in flagmasksfile:
            parts = line.split(" ")

            col = ord(parts[0][0]) - ord('A')
            row = int(parts[0][2])
            rMask = int(parts[1], 2)
            mMask = int(parts[2], 2)

            regionsVisibleBitmasks[col][row] = rMask
            modificationsTriggeredBitmasks[col][row] = mMask
    flagmasksfile.close()

def stitchAndSave(tiles, filename):
    missingtiles = False
    for col in range(0, NUM_COLUMNS):
        for row in range(0, NUM_ROWS):
            if(tiles[col][row] == None):
                colLetter = chr(ord('A') + col)
                print("ERROR: you are missing the required tile for column " + str(colLetter) + ", row " + str(row))
                missingtiles = True
    if(missingtiles):
        exit()

    patchDim = tiles[0][0].width
    fullMap = Image.new('RGB', (patchDim * NUM_COLUMNS, patchDim * NUM_ROWS))
    
    for col in range(0, NUM_COLUMNS):
        colchar = chr(ord('A') + col)
        print("Stitching column " + colchar)
        for row in range(0, NUM_ROWS):
            fullMap.paste(im=tiles[col][row], box=(col * patchDim, row * patchDim))
    
    print("Saving image... (this could take a while if you've selected a high level of detail)")
    fullMap.save(filename, "PNG")
    print("Finished!")

def searchDir(dirPath, tileArray, regionsVisibleFlags, modificationsTriggeredFlags):
    for filename in listdir(dirPath):
        if(filename.endswith(".png")):
            col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags = getTileInfo(filename)
            if(tileArray[col][row] == None):
                regionMask = regionsVisibleBitmasks[col][row]
                if((regionMask & tileRegionsVisibleFlags) == (regionMask & regionsVisibleFlags)):
                    modsMask = modificationsTriggeredBitmasks[col][row]
                    if((modsMask & tileModificationsTriggeredFlags) == (modsMask & modificationsTriggeredFlags)):
                        tileArray[col][row] = Image.open(dirPath + "/" + filename)

def main():
    parser = ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("-o", "--output", dest="outputImageName", default="output.png",
                        help="save generated image to FILE.", metavar="FILE")
    parser.add_argument("-l", "--lod", dest="lod", default=0, type=int,
                        help="Level of detail of the output image, from 0 (highest) to 3 (lowest).")
    parser.add_argument("-r", "--regions", dest="regionsVisible", default="all", type=str,
                        help="a series of 15 1s or 0s indicating which regions are visible (i.e. which towers have been activated). You can also use the aliases \"all\" or \"none\"",
                        metavar="NNNNNNNNNNNNNNN")
    parser.add_argument("-t", "--tarreytown", dest="ttState", default=5, type=int,
                        help="State of Tarrey Town, from 0 (nonexistent) to 5 (fully built)", metavar="STATE")
    parser.add_argument("-b", "--bridge", dest="bridgeState", choices=["up", "down"], default="down",
                        help="State of the Eldin Bridge (up or down)")

    args = parser.parse_args(["../Legend of Zelda - Breath of the Wild"])

    #folder path
    if(not path.exists(args.folder)):
        print("ERROR: folder \"" + args.folder + "\" does not exist.")
        exit()

    hasMapFolder = False
    for filename in listdir(args.folder):
        if(filename == "Map" or filename == "Map1" or
           filename == "Map2" or filename == "Map3"):
            hasMapFolder = True
    if(not hasMapFolder):
        print("ERROR: Invalid folder selection. Folder should contain at least one of the following folders: Map, Map1, Map2, Map3")
        exit()

    fullpath = ""
    if(args.lod == 0):
        fullpath = path.join(args.folder, "Map")
    else:
        fullpath = path.join(args.folder, "Map" + str(args.lod))

    if(not path.exists(fullpath)):
        print("ERROR: You do not have the correct files for level of detail " + str(args.lod) + ".")
        exit()

    # output
    outputFilename = args.outputImageName
    if(not outputFilename.endswith(".png")):
        outputFilename += ".png"

    # flags
    regVisString = args.regionsVisible
    if(regVisString == "all"):
        regVisString = "111111111111111"
    elif(regVisString == "none"):
        regVisString ="000000000000000"

    regionsVisibleFlags = int(regVisString, 2)
    modificationsTriggeredFlags = 0
    if(args.bridgeState == "down"):
        modificationsTriggeredFlags |= 0b100000
    if(args.ttState != 0):
        for i in range(0, args.ttState):
            modificationsTriggeredFlags |= (0b1 << i)

    if((regionsVisibleFlags & ELDIN_BRIDGE_VISIBILITY_BIT) == 0):
        modificationsTriggeredFlags &= ~0b100000
    if((regionsVisibleFlags & TARREY_TOWN_VISIBILITY_BIT) == 0):
        modificationsTriggeredFlags &= ~0b011111

    #Print summary
    print("Paramaters being used:")
    if(args.lod == 0):
        print("Level of detail: 0 (highest)")
    elif(args.lod == 3):
        print("Level of detail: 3 (lowest)")
    else:
        print("Level of detail: " + str(args.lod))

    if(regionsVisibleFlags == ALL_REGIONS_VISIBLE):
        print("All regions visible")
    elif(regionsVisibleFlags == 0):
        print("No regions visible")
    else:
        print("Regions visible: " + args.regionsVisible)

    if((regionsVisibleFlags & TARREY_TOWN_VISIBILITY_BIT) == 0):
        print("Tarrey Town is not visible")
    elif(args.ttState == 5):
        print("Tarrey Town is complete")
    elif(args.ttState == 0):
        print("Tarrey Town has not begun being built")
    else:
        print("Tarrey Town is in state " + str(args.ttState))

    if((regionsVisibleFlags & ELDIN_BRIDGE_VISIBILITY_BIT) == 0):
        print("Eldin bridge is not visible")
    else:
        print("Eldin bridge is " + args.bridgeState)

    loadBitmasks()

    tiles = make2DDict()

    searchDir(fullpath, tiles, regionsVisibleFlags, modificationsTriggeredFlags)
    if(path.exists(fullpath + "/Empty")):
        searchDir(fullpath + "/Empty", tiles, regionsVisibleFlags, modificationsTriggeredFlags)
    if(path.exists(fullpath + "/Full")):
        searchDir(fullpath + "/Full", tiles, regionsVisibleFlags, modificationsTriggeredFlags)

    stitchAndSave(tiles, outputFilename)

main()
