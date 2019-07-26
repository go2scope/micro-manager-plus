# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to support reading micro-manager multi-dimensional
data sets.

"""
import json
import os
import cv2
import numpy as np


class SummaryMeta:
    """
    Summary metadata represents the entire data set
    Assumed to be set before acquisition starts
    """
    # MANDATORY
    # ---------
    PREFIX = "Prefix"  # serves as a "name"
    SOURCE = "Source"  # source application

    # Multi-D coordinate space (sparse)
    # this represents intended coordinate space limits
    # it is OK if some images are missing
    CHANNELS = "Channels"
    SLICES = "Slices"
    FRAMES = "Frames"
    POSITIONS = "Positions"
    CHANNEL_NAMES = "ChNames"
    CHANNEL_COLORS = "Colors"

    STAGE_POSITIONS = "StagePositions"

    # image format
    WIDTH = "WIDTH"
    HEIGHT = "HEIGHT"
    PIXEL_TYPE = "PixelType"
    PIXEL_SIZE = "PixelSize_um"
    BIT_DEPTH = "BitDepth"
    PIXEL_ASPECT = "PixelAspect"


class ImageMeta:
    WIDTH = "Width"
    HEIGHT = "Height"
    CHANNEL = "Channel"
    CHANNEL_NAME = "Channel"  # ?? duplicate
    FRAME = "Frame"  # what about FRAME_INDEX?
    SLICE = "Slice"  # what about SLICE_INDEX?
    CHANNEL_INDEX = "ChannelIndex"
    SLICE_INDEX = "SliceIndex"
    FRAME_INDEX = "FrameIndex"
    POS_NAME = "PositionName"
    POS_INDEX = "PositionIndex"
    XUM = "XPositionUm"
    YUM = "YPositionUm"
    ZUM = "ZPositionUm"

    FILE_NAME = "FileName"

    ELAPSED_TIME_MS = "ElapsedTime-ms"


class StagePositionMeta:
    LABEL = "Label"
    GRID_ROW = "GridRow"
    GRID_COL = "GridCol"


class Values:
    PIX_TYPE_GRAY_32 = "GRAY32"
    PIX_TYPE_GRAY_16 = "GRAY16"
    PIX_TYPE_GRAY_8 = "GRAY8"
    PIX_TYPE_RGB_32 = "RGB32"
    PIX_TYPE_RGB_64 = "RGB64"


class G2SPosDataset:
    """ Micro-manager dataset
    
        Represents a multi-dimensional image.
        Three coordinates: frame-channel-slice
        
    """

    # constants
    METADATA_FILE_NAME = 'metadata.txt'
    KEY_SUMMARY = 'Summary'

    def __init__(self):
        """ Constructor. Defines an empty data set. """
        self._path = ""
        self._name = ""
        self._frames = dict()

        self._z_slices = 0
        self._channel_names = []
        self._frames = 0
        self._positions = []

        self._pixel_size_um = 1.0
        self._metadata = dict()

    def load_meta(self, dir_path: str):
        """ Loads the entire data set, including images
        """

        self._path = dir_path
        with open(os.path.join(self._path, G2SPosDataset.METADATA_FILE_NAME)) as md_file:
            self._metadata = json.load(md_file)

        summary = self._metadata[G2SPosDataset.KEY_SUMMARY]

        self._name = summary[SummaryMeta.PREFIX]
        self._pixel_size_um = summary[SummaryMeta.PIXEL_SIZE]
        self._channel_names = summary[SummaryMeta.CHANNEL_NAMES]
        self._z_slices = summary[SummaryMeta.SLICES]
        self._frames = summary[SummaryMeta.FRAMES]
        self._positions = summary[SummaryMeta.POSITIONS]

    @staticmethod
    def _frame_key(channel: int, z_slice: int, frame: int) -> str:
        """ Returns frame key string based on the three integer coordinates """
        return "FrameKey" + "-" + str(frame) + "-" + str(channel) + "-" + str(z_slice)

    def name(self):
        return self._name

    def num_frames(self) -> int:
        return self._frames

    def num_channels(self) -> int:
        return len(self._channel_names)

    def num_z_slices(self) -> int:
        return self._z_slices

    def channel_names(self) -> []:
        return self._channel_names

    def pixel_size(self) -> float:
        return self._pixel_size_um

    def summary_metadata(self) -> dict:
        return self._metadata[G2SPosDataset.KEY_SUMMARY]

    def image_metadata(self, channel_index=0, channel_name="", z_index=0, t_index=0) -> dict:
        ch_index = channel_index
        if channel_name:
            ch_index = self._channel_names.index(channel_name)

        if ch_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or\
                t_index not in range(0, self._frames):
            raise Exception("Invalid image coordinates: channel=%d, slice=%d, frame=%d" % (ch_index, z_index, t_index))

        return self._metadata[G2SPosDataset._frame_key(ch_index, z_index, t_index)]

    def image_pixels(self, channel_index=0, channel_name="", z_index=0, t_index=0) -> np.array:
        ch_index = channel_index
        if channel_name:
            ch_index = self._channel_names.index(channel_name)

        if ch_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or\
                t_index not in range(0, self._frames):
            raise Exception("Invalid image coordinates: channel=%d, slice=%d, frame=%d" % (ch_index, z_index, t_index))

        image_path = os.path.join(self._path, self._metadata[G2SPosDataset._frame_key(channel_index, z_index, t_index)]
        [ImageMeta.FILE_NAME])
        cv2_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if cv2_image is None:
            raise Exception("Invalid image reference: " + image_path)
        return cv2_image


class G2SDataset:
    def __init__(self, path):
        """ Constructor. Defines an empty data set. """
        self._positions = []
        self.load_meta(path)

    def load_meta(self, dir_path: str):
        """ Loads the metadata
        """
        self._positions = []  # reset contents

        list_of_dirs = [name for name in os.listdir(dir_path) if os.path.isdir(os.path.join(dir_path, name))]
        for pos_dir in list_of_dirs:
            self._positions.append(G2SPosDataset().load_meta(pos_dir))

        if not len(self._positions):
            raise Exception("Micro-manager data set not identified in " + dir_path)

    def name(self):
        return self._positions[0].name()

    def num_positions(self):
        return len(self._positions)

    def num_frames(self) -> int:
        return self._positions[0].num_frames()

    def num_channels(self) -> int:
        return len(self._positions[0].num_channels())

    def num_z_slices(self) -> int:
        return self._positions[0].num_z_slices()

    def channel_names(self) -> []:
        return self._positions[0].channel_names()

    def pixel_size(self) -> float:
        return self._positions[0].pixel_size()

    def summary_metadata(self) -> dict:
        return self._positions[0].summary_metadata()

    def image_metadata(self, position_index=0, channel_index=0, channel_name="", z_index=0, t_index=0) -> dict:
        return self._positions[position_index].image_metadata(channel_index, channel_name, z_index, t_index)

    def image_pixels(self, position_index=0, channel_index=0, channel_name="", z_index=0, t_index=0) -> np.array:
        return self._positions[position_index].image_pixels(channel_index, channel_name, z_index, t_index)


