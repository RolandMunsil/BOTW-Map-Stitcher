# Introduction
_Spriter's Resource_ user [Random Talking Brush](https://www.spriters-resource.com/submitter/Random+Talking+Bush/)
extracted the images used to display the map in _Legend of Zelda: Breath of the Wild_, but it's all divided up
into square tiles, and there are also separate tile variations for different states of the map. 
This Python 3 script stitches together the tiles into single images.

# Basic Use
First, make sure you have the actual map files (download [here](https://www.spriters-resource.com/wii_u/thelegendofzeldabreathofthewild/)).
Depending on what you want to do, you don't need to download them all.
 * The "Map (Full)" archive contains everything needed to make a map at the highest quality (24,000x20,000 pixels) with all regions visible, 
   although it will NOT have the complete Tarrey Town and Eldin Bridge will be up.
    - To get complete Tarrey Town and lowered Eldin Bridge, you can additionally download the "Map Variants (I-L)" archive.
 * The "Map (Lower-Resolution)" archive contains everything needed to make 100% complete maps 
   (i.e. all regions visible, Tarrey Town complete, and Eldin Bridge down) at any lower resolution
 * The Variants archives contain the additional tiles needed to make highest-quality maps with regions missing.
 * The "Map (Empty)" archive contains everything needed to make
   a completely empty map (i.e. just the background pattern and borders).
 
**VERY IMPORTANT!!!**: Be sure to extract them all into the _same folder_. The files should be structured like this:
```
Legend of Zelda - Breath of the Wild\
  Map\
    Empty\
    Full\
    (346 PNGs)
  Map1\
    Empty\
    Full\
    (346 PNGs)
  Map2\
    Empty\
    Full\
    (346 PNGs)
  Map3\
    Empty\
    Full\
    (346 PNGs)
```
 
Finally, download the python script and flagmasks.txt. You can run the script like this:
```
python stitchmap.py <folder containing Map, Map1, etc.> [-o output_filename] [-l level_of_detail] [-r visible_regions] [-t tarrey_town_state] [-b bridge_state]
```
For more details on the parameters, see the "Argument Details" section. However, here are parameters for some of the most common commands:
  * Full-quality map with just all regions visible (no tarrey town, bridge up): `<folder> -l0 -r all -t0 -bup`
  
  * Full-quality 100% complete map (tarrey town complete, bridge down): `<folder> -l0 -r all -t5 -bdown`
  * Lower-quality 100% complete map (tarrey town complete, bridge down): `<folder> -l1 -r all -t5 -bdown`
  * Lowest-quality 100% complete map (tarrey town complete, bridge down) `<folder> -l3 -r all -t5 -bdown`
  
  * Full-quality empty map (just the blue background pattern) `<folder> -l0 -r none`
  * Lower-quality empty map (just the blue background pattern) `<folder> -l1 -r none`
 
 # Argument Details
 TODO
 
