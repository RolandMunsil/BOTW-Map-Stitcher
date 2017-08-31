from PIL import Image
from os import listdir
from functools import reduce
from argparse import ArgumentParser
from os import path

ALL_REGIONS_VISIBLE: int = 0b111111111111111 #15 bits
ALL_MODIFICATIONS_TRIGGERED: int = 0b111111 #6 bits
NUM_COLUMNS: int = 12
NUM_ROWS: int = 10
ELDIN_BRIDGE_VISIBILITY_BIT = 0b000001000000000
TARREY_TOWN_VISIBILITY_BIT =  0b000010000000000

regionsVisibleBitmasks = None
modificationsTriggeredBitmasks = None

def getTileInfo(filename: str):
    #remove extension
    filename = filename.split('.')[0]
    underscoreparts = filename.split('_')
    loc: str = underscoreparts[1][0:3]
    col: int = ord(loc[0]) - ord('A')
    row: int = int(loc[2])

    tileRegionsVisibleFlags: int = None
    tileModificationsTriggeredFlags: int = None
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

        possibleModsTriggeredFlags: str = underscoreparts[1][4:]
        if(possibleModsTriggeredFlags != "" and possibleModsTriggeredFlags != None):
            tileModificationsTriggeredFlags = int(possibleModsTriggeredFlags)
        else:
            tileModificationsTriggeredFlags = 0

    return (col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags)

def make2DDict(initialValue = None):
    tiles = {}
    for col in range(0, NUM_COLUMNS):
        tiles[col] = {}
        for row in range(0, NUM_ROWS):
            tiles[col][row] = initialValue
    return tiles

def getOrReturnNone(bitmasks, col, row) -> int:
    if(col < 0 or row < 0 or col >= NUM_COLUMNS or row >= NUM_ROWS):
        return None
    else:
        return bitmasks[col][row]

def hasSingleFlag(bm) -> bool:
    return bm != 0 and ((bm & (bm - 1)) == 0)

def getRegionsVisibileBitmasks(folderpath: str):
    bitmasks = make2DDict(None)
    for filename in listdir(folderpath):
        if(filename.endswith(".png")):
            col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags = getTileInfo(filename)
            if(tileRegionsVisibleFlags == None):
                continue
            if(bitmasks[col][row] == None):
                bitmasks[col][row] = 0
            bitmasks[col][row] |= int(tileRegionsVisibleFlags)
    
    nonesStillExist = True
    while(nonesStillExist):
        nonesStillExist = False
        for col in range(0, NUM_COLUMNS):
            for row in range(0, NUM_ROWS):
                if(bitmasks[col][row] == None):
                    nonesStillExist = True
                    # get masks for surrounding tiles
                    surroundingMasks = [getOrReturnNone(bitmasks, c, r) for c in range(col-1,col+2) for r in range(row-1,row+2)]
                    # remove nones
                    surroundingMasksFiltered = list(filter(None, surroundingMasks))
                    if(len(surroundingMasksFiltered) > 0):
                        #try to find common single bit
                        commonBits = reduce(lambda b1, b2: b1 & b2, surroundingMasksFiltered)
                        if(hasSingleFlag(commonBits)):
                            bitmasks[col][row] = commonBits

    return bitmasks

def getModificationsTriggeredBitmasks(folderpath: str):
    bitmasks = make2DDict(initialValue=0)

    for filename in listdir(folderpath):
        if(filename.endswith(".png")):
            col, row, tileRegionsVisibleFlags, tileModificationsTriggeredFlags = getTileInfo(filename)
            bitmasks[col][row] |= tileModificationsTriggeredFlags
    return bitmasks

def stitchAndSave(tiles, filename):
    missingtiles = False
    for col in range(0, NUM_COLUMNS):
        for row in range(0, NUM_ROWS):
            if(tiles[col][row] == None):
                colLetter = chr(ord('A') + col)
                print(f"ERROR: you are missing the required tile for column {colLetter}, row {row}")
                missingtiles = True
    if(missingtiles):
        exit()

    patchDim = tiles[0][0].width
    fullMap = Image.new('RGB', (patchDim * NUM_COLUMNS, patchDim * NUM_ROWS))
    
    for col in range(0, NUM_COLUMNS):
        print(f"Stitching column {col}")
        for row in range(0, NUM_ROWS):
            fullMap.paste(im=tiles[col][row], box=(col * patchDim, row * patchDim))
    
    print("Saving image... (this could take a while if you've selected a high level of detail)")
    fullMap.save(filename, "PNG")
    print("Finished!")

def searchDir(dirPath: str, tileArray, regionsVisibleFlags: int, modificationsTriggeredFlags: int):
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
    parser.add_argument("-r", "--regions", dest="regionsVisible", default="111111111111111", type=str,
                        help="a series of 15 1s or 0s indicating which regions are visible (i.e. which towers have been activated)",
                        metavar="NNNNNNNNNNNNNNN")
    parser.add_argument("-t", "--tarreytown", dest="ttState", default=5, type=int,
                        help="State of Tarrey Town, from 0 (nonexistent) to 5 (fully built)", metavar="STATE")
    parser.add_argument("-b", "--bridge", dest="bridgeState", choices=["up", "down"], default="down",
                        help="State of the Eldin Bridge (up or down)")

    args = parser.parse_args(["../Legend of Zelda - Breath of the Wild"])

    #folder path
    if(not path.exists(args.folder)):
        print(f"ERROR: folder \"{args.folder}\" does not exist.")
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
        print(f"ERROR: You do not have the correct files for level of detail {args.lod}.")
        exit()

    # output
    outputFilename = args.outputImageName
    if(not outputFilename.endswith(".png")):
        outputFilename += ".png"

    # flags
    regionsVisibleFlags = int(args.regionsVisible, 2)
    modificationsTriggeredFlags = 0
    if(args.bridgeState == "down"):
        modificationsTriggeredFlags |= 0b100000
    if(args.ttState != 0):
        for i in range(0, args.ttState):
            modificationsTriggeredFlags |= (0b1 << i)

    if((regionsVisibleFlags & ELDIN_BRIDGE_VISIBILITY_BIT) == 0):
        modificationsTriggeredFlags &= 0b011111
    if((regionsVisibleFlags & TARREY_TOWN_VISIBILITY_BIT) == 0):
        modificationsTriggeredFlags &= 0b100000

    global regionsVisibleBitmasks
    global modificationsTriggeredBitmasks
    regionsVisibleBitmasks = getRegionsVisibileBitmasks(fullpath)
    modificationsTriggeredBitmasks = getModificationsTriggeredBitmasks(fullpath)

    #flagmasksfile = open("flagmasks.txt","w+")
    #for col in range(0, NUM_COLUMNS):
    #    for row in range(0, NUM_ROWS):
    #        c = chr(ord('A') + col)
    #        r = "{:0>15b}".format(regionsVisibleBitmasks[col][row])
    #        e = "{:0>6b}".format(modificationsTriggeredBitmasks[col][row])
    #        flagmasksfile.write(f"{c}-{row} {r} {e}\n")
    #flagmasksfile.close()
    

    tiles = make2DDict()

    searchDir(fullpath, tiles, regionsVisibleFlags, modificationsTriggeredFlags)
    if(path.exists(fullpath + "/Empty")):
        searchDir(fullpath + "/Empty", tiles, regionsVisibleFlags, modificationsTriggeredFlags)
    if(path.exists(fullpath + "/Full")):
        searchDir(fullpath + "/Full", tiles, regionsVisibleFlags, modificationsTriggeredFlags)

    stitchAndSave(tiles, outputFilename)

main()
