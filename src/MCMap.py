import os
import sys
import zlib
import nbt
import random
import time
import logging
from io import BytesIO
import sqlite3

import mcvars
import serialize
from MCChunk import MCChunk
from itemstack import *
from tile_entities import te_convert
from entities import e_convert
from block import *

"""Minecraft map"""
class MCMap:
    """Minecraft Map representation

    Args:
        world_path: path to world directory
    """
    def __init__(self, world_path):
        self.world_path = os.path.join(world_path, "region")
        self.chunk_positions = []

        # Parse region files (Region and Anvil) files in "region" folder
        for ext in ["mca", "mcr"]:
            filenames = [i for i in os.listdir(self.world_path)
                         if i.endswith("." + ext)]
            if len(filenames) > 0:
                self.ext = ext
                break

        for filename in filenames:
            # Parse filename r.[region X].[region Z].mc(a/r)
            _r, regionXstr, regionZstr, _ext = filename.split(".")

            startChunkX = int(regionXstr) * mcvars.REGION_CHUNK_LENGTH
            startChunkZ = int(regionZstr) * mcvars.REGION_CHUNK_LENGTH

            with open(os.path.join(self.world_path, filename), "rb") as regionFile:
                for regionChunkXPos in range(startChunkX, startChunkX + mcvars.REGION_CHUNK_LENGTH):
                    for regionChunkZPos in range(startChunkZ, startChunkZ + mcvars.REGION_CHUNK_LENGTH):
                        offset = ((regionChunkXPos % mcvars.REGION_CHUNK_LENGTH) +
                                  mcvars.REGION_CHUNK_LENGTH * 
                                    (regionChunkZPos % mcvars.REGION_CHUNK_LENGTH)
                                ) * 4
                        regionFile.seek(offset)
                        # do not process chunk if empty
                        if serialize.bytesToInt(regionFile.read(3)) != 0:
                            self.chunk_positions.append((regionChunkXPos, regionChunkZPos))

    def getChunk(self, x, z):
        return MCChunk(x, z, self.world_path, self.ext)

    def getBlocksIterator(self):
        num_chunks = len(self.chunk_positions)
        chunk_index = 0
        currentTime = time.time()
        for x, z in self.chunk_positions:
            # Only calculate time for every Nth chunk
            if chunk_index % 16 * 16 == 0:
                if chunk_index > 0:
                    timeDifference = time.time() - currentTime
                    timeRemaining = ((num_chunks * timeDifference) / chunk_index) - timeDifference  # time remaining
                    timeRemainingStr = time.strftime("%H:%M:%S", time.gmtime(timeRemaining))
                else:
                    timeRemainingStr = "??:??:??"
                print("Processed %d / %d chunks, ETA %s h:m:s" %
                      (chunk_index, num_chunks, timeRemainingStr), end="\r")
                sys.stdout.flush()
            chunk_index += 1
            blocks = self.getChunk(x, z).blocks
            for block in blocks:
                yield block
        print()
