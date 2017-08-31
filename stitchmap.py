from PIL import Image
from os import listdir
from functools import reduce
from argparse import ArgumentParser
from os import path

ALL_TOWERS_ACTIVATED: int = 0b111111111111111 #15 bits
ALL_CHANGES_TRIGGERED: int = 0b111111 #6 bits
NUM_COLUMNS: int = 12
NUM_ROWS: int = 10
ELDIN_BRIDGE_VISIBILITY_BIT = 0b000001000000000
TARREY_TOWN_VISIBILITY_BIT =  0b000010000000000

regionBitmasks = None
extrasBitmasks = None

def getTileInfo(filename: str):
    #remove extension
    filename = filename.split('.')[0]
    underscoreparts = filename.split('_')
    loc: str = underscoreparts[1][0:3]
    col: int = ord(loc[0]) - ord('A')
    row: int = int(loc[2])

    regionVisibilityFlags: int = None
    otherMapFlags: int = None
    if(len(underscoreparts) > 2):
        flagparts = underscoreparts[2].split('-')
        if(len(flagparts) > 1):
            regionVisibilityFlags = int(flagparts[0])
            otherMapFlags = int(flagparts[1])
        else:
            regionVisibilityFlags = int(underscoreparts[2])
            otherMapFlags = 0
    else:
        if(regionBitmasks == None):
            regionVisibilityFlags = None
        else:
            regionVisibilityFlags = regionBitmasks[col][row]

        possibleOtherFlags: str = underscoreparts[1][4:]
        if(possibleOtherFlags != "" and possibleOtherFlags != None):
            otherMapFlags = int(possibleOtherFlags)
        else:
            otherMapFlags = 0

    return (col, row, regionVisibilityFlags, otherMapFlags)

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

def getRegionBitMasks(folderpath: str):
    bitmasks = make2DDict(None)
    for filename in listdir(folderpath):
        if(filename.endswith(".png")):
            col, row, regionVisibilityFlags, otherMapFlags = getTileInfo(filename)
            if(regionVisibilityFlags == None):
                continue
            if(bitmasks[col][row] == None):
                bitmasks[col][row] = 0
            bitmasks[col][row] |= int(regionVisibilityFlags)
    
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

def getExtrasBitMasks(folderpath: str):
    bitmasks = make2DDict(initialValue=0)

    for filename in listdir(folderpath):
        if(filename.endswith(".png")):
            col, row, regionVisibilityFlags, otherMapFlags = getTileInfo(filename)
            bitmasks[col][row] |= otherMapFlags
    return bitmasks

def stitchAndSave(tiles, filename):
    patchDim = tiles[0][0].width
    fullMap = Image.new('RGB', (patchDim * NUM_COLUMNS, patchDim * NUM_ROWS))
    
    for col in range(0, NUM_COLUMNS):
        for row in range(0, NUM_ROWS):
            fullMap.paste(im=tiles[col][row], box=(col * patchDim, row * patchDim))
    
    fullMap.save(filename, "PNG")

def searchDir(dirPath: str, tileArray, activatedTowerFlags: int, otherFlags: int):
    for filename in listdir(dirPath):
        if(filename.endswith(".png")):
            col, row, regionVisibilityFlags, otherMapFlags = getTileInfo(filename)
            if(tileArray[col][row] == None):
                mask = regionBitmasks[col][row]
                if((mask & regionVisibilityFlags) == (mask & activatedTowerFlags)):
                    extrasMask = extrasBitmasks[col][row]
                    if((extrasMask & otherMapFlags) == (extrasMask & otherFlags)):
                        tileArray[col][row] = Image.open(dirPath + "/" + filename)

def main():
    parser = ArgumentParser()
    parser.add_argument("folder")
    parser.add_argument("-o", "--output", dest="outputImageName", default="output",
                        help="save generated image to FILE.", metavar="FILE")
    parser.add_argument("-l", "--lod", dest="lod", default=0, type=int,
                        help="Level of detail of the output image, from 0 (highest) to 3 (lowest).")
    parser.add_argument("-a", "--towers", dest="towersActivated", default="111111111111111", type=str,
                        help="a series of 15 1s or 0s indicating which towers have been activated",
                        metavar="NNNNNNNNNNNNNNN")
    parser.add_argument("-t", "--tarreytown", dest="ttState", default=5, type=int,
                        help="State of Tarrey Town, from 0 (nonexistent) to 5 (fully built)", metavar="STATE")
    parser.add_argument("-b", "--bridge", dest="bridgeState", choices=["up", "down"], default="down",
                        help="State of the Eldin Bridge (up or down)")

    args = parser.parse_args()

    fullpath = ""
    if(args.lod == 0):
        fullpath = path.join(args.folder, "Map")
    else:
        fullpath = path.join(args.folder, "Map" + str(args.lod))

    outputFilename = args.outputImageName
    if(not outputFilename.endswith(".png")):
        outputFilename += ".png"

    towerFlags = int(args.towersActivated, 2)
    otherFlags = 0
    if(args.bridgeState == "down"):
        otherFlags |= 0b100000
    if(args.ttState != 0):
        for i in range(0, args.ttState):
            otherFlags |= (0b1 << i)

    if((towerFlags & ELDIN_BRIDGE_VISIBILITY_BIT) == 0):
        otherFlags &= 0b011111
    if((towerFlags & TARREY_TOWN_VISIBILITY_BIT) == 0):
        otherFlags &= 0b100000

    global regionBitmasks
    global extrasBitmasks
    regionBitmasks = getRegionBitMasks(fullpath)
    extrasBitmasks = getExtrasBitMasks(fullpath)

    #for col in range(0, NUM_COLUMNS):
    #    for row in range(0, NUM_ROWS):
    #        c = chr(ord('A') + col)
    #        r = "{:0>15b}".format(regionBitmasks[col][row])
    #        e = "{:0>6b}".format(extrasBitmasks[col][row])
    #        print(f"{c}-{row} | {r} | {e}")


    tiles = make2DDict()

    searchDir(fullpath, tiles, towerFlags, otherFlags)
    searchDir(fullpath + "/Empty", tiles, towerFlags, otherFlags)
    searchDir(fullpath + "/Full", tiles, towerFlags, otherFlags)

    stitchAndSave(tiles, outputFilename)

main()
