from PIL import Image
from os import listdir
from functools import reduce

ALL_REGIONS_UNLOCKED: int = 0b111111111111111 #15 bits
NUM_COLUMNS: int = 12
NUM_ROWS: int = 10
regionBitmasks = None
extrasBitmasks = None

basePath: str = "Legend of Zelda - Breath of the Wild"
unlockedRegions: int = 0b111111111111111
mapFlags: int = 0b100011
lod: int = 1

def getTileInfo(filename: str, ):
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

def stitchAndSave(tiles):
    patchDim = tiles[0][0].width
    fullMap = Image.new('RGB', (patchDim * NUM_COLUMNS, patchDim * NUM_ROWS))
    
    for col in range(0, NUM_COLUMNS):
        for row in range(0, NUM_ROWS):
            fullMap.paste(im=tiles[col][row], box=(col * patchDim, row * patchDim))
    
    fullMap.save("stitched.png", "PNG")

def searchDir(dirPath: str, tileArray):
    for filename in listdir(dirPath):
        if(filename.endswith(".png")):
            col, row, regionVisibilityFlags, otherMapFlags = getTileInfo(filename)
            if(tileArray[col][row] == None):
                mask = regionBitmasks[col][row]
                if((mask & regionVisibilityFlags) == (mask & unlockedRegions)):
                    extrasMask = extrasBitmasks[col][row]
                    if((extrasMask & otherMapFlags) == (extrasMask & mapFlags)):
                        tileArray[col][row] = Image.open(dirPath + "/" + filename)

def main():
    fullpath = ""
    if(lod == 0):
        fullpath = basePath + "/Map"
    else:
        fullpath = basePath + "/Map" + str(lod)

    global regionBitmasks
    global extrasBitmasks
    regionBitmasks = getRegionBitMasks(fullpath)
    extrasBitmasks = getExtrasBitMasks(fullpath)

    tiles = make2DDict()

    searchDir(fullpath, tiles)
    searchDir(fullpath + "/Empty", tiles)
    searchDir(fullpath + "/Full", tiles)

    stitchAndSave(tiles)

main()
