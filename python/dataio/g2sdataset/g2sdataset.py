# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to support reading micro-manager multi-dimensional
data sets.

"""
import json
import os
from json import JSONDecodeError

import cv2
import numpy as np


class G2SDataError(Exception):
    pass


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
    WIDTH = "Width"
    HEIGHT = "Height"
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
    PIX_TYPE_NONE = "NONE"
    PIX_TYPE_GRAY_32 = "GRAY32"
    PIX_TYPE_GRAY_16 = "GRAY16"
    PIX_TYPE_GRAY_8 = "GRAY8"
    PIX_TYPE_RGB_32 = "RGB32"
    PIX_TYPE_RGB_64 = "RGB64"


class G2SPosDatasetReader:
    """ Micro-manager dataio
    
        Represents a multi-dimensional image.
        Three coordinates: frame-channel-slice
        
    """

    # constants
    METADATA_FILE_NAME = 'metadata.txt'
    KEY_SUMMARY = 'Summary'

    def __init__(self, path):
        """ Constructor. Defines an empty data set. """
        self._path = path
        self._name = ""

        self._z_slices = 0
        self._channel_names = []
        self._frames = 0
        self._positions = []
        self._width = 0
        self._height = 0
        self._pixel_type = Values.PIX_TYPE_NONE
        self._bit_depth = 0

        self._pixel_size_um = 1.0
        self._metadata = dict()
        self._load_meta()

    def _load_meta(self):
        """ Loads the entire data set, including images
        """

        with open(os.path.join(self._path, G2SPosDatasetReader.METADATA_FILE_NAME)) as md_file:
            # there is a strange bug in some of the micro-manager datasets where closing "}" is
            # missing, so we try to fix
            mdstr = md_file.read()
            try:
                self._metadata = json.loads(mdstr)
            except JSONDecodeError:
                mdstr += '}'
                self._metadata = json.loads(mdstr)

        summary = self._metadata[G2SPosDatasetReader.KEY_SUMMARY]

        self._name = summary[SummaryMeta.PREFIX]
        self._pixel_size_um = summary[SummaryMeta.PIXEL_SIZE]
        self._channel_names = summary[SummaryMeta.CHANNEL_NAMES]
        self._z_slices = summary[SummaryMeta.SLICES]
        self._frames = summary[SummaryMeta.FRAMES]
        self._positions = summary[SummaryMeta.POSITIONS]
        self._width = summary[SummaryMeta.WIDTH]
        self._height = summary[SummaryMeta.HEIGHT]
        self._pixel_type = summary[SummaryMeta.PIXEL_TYPE]
        self._bit_depth = summary[SummaryMeta.BIT_DEPTH]

    @staticmethod
    def get_frame_key(channel: int, z_slice: int, frame: int) -> str:
        """ Returns frame key string based on the three integer coordinates """
        return "FrameKey" + "-" + str(frame) + "-" + str(channel) + "-" + str(z_slice)

    def name(self):
        return self._name

    def width(self):
        return self._width

    def height(self):
        return self._height

    def pixel_type(self):
        return self._pixel_type

    def bit_depth(self):
        return self._bit_depth

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

    def position_index(self) -> int:
        """
        Returns position index of the positional sub-dataio.
        This information is stored only in image meta, so we have to search through image metadata
        until we find first one. Search is necessary because particular coordinates are not guaranteed to be available
        """
        for fk in self._metadata.keys():
            if fk.startswith("FrameKey"):
                return int(self._metadata[fk][ImageMeta.POS_INDEX])

        raise G2SDataError("Position index not available in image metadata.")

    def summary_metadata(self) -> dict:
        return self._metadata[G2SPosDatasetReader.KEY_SUMMARY]

    def _get_channel_index(self, cindex: int, cname: str) -> int:
        if cname:
            try:
                return self._channel_names.index(cname)
            except Exception:
                raise G2SDataError("Invalid channel name: " + cname)
        else:
            return cindex

    def image_metadata(self, channel_index=0, channel_name="", z_index=0, t_index=0) -> dict:
        ch_index = self._get_channel_index(channel_index, channel_name)
        if ch_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or \
                t_index not in range(0, self._frames):
            raise G2SDataError("Invalid image coordinates: channel=%d, slice=%d, frame=%d" % (ch_index, z_index, t_index))

        try:
            md = self._metadata[G2SPosDatasetReader.get_frame_key(ch_index, z_index, t_index)]
        except Exception as err:
            raise G2SDataError("Frame key not available in metadata: " + err.__str__())

        return md

    def image_pixels(self, channel_index=0, channel_name="", z_index=0, t_index=0) -> np.array:
        ch_index = self._get_channel_index(channel_index, channel_name)
        if ch_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or \
                t_index not in range(0, self._frames):
            raise G2SDataError("Invalid image coordinates: channel=%d, slice=%d, frame=%d" % (ch_index, z_index, t_index))

        image_path = os.path.join(self._path,
                                  self._metadata[G2SPosDatasetReader.get_frame_key(channel_index, z_index, t_index)][ImageMeta.FILE_NAME])
        cv2_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if cv2_image is None:
            raise G2SDataError("Invalid image reference: " + image_path)
        return cv2_image


class G2SDatasetReader:
    def __init__(self, path: str):
        """ Constructor. Defines an empty data set.
            Alternatively it can load data set right away if the path is supplied
        """
        self._positions = []
        self._path = path
        self._name = ""
        self._load_meta()

    def _load_meta(self):
        """ Loads the metadata
        """
        self._positions = []  # reset contents

        list_of_dirs = [name for name in os.listdir(self._path) if os.path.isdir(os.path.join(self._path, name))]
        self._positions = [None] * len(list_of_dirs)
        for pos_dir in list_of_dirs:
            pds = G2SPosDatasetReader(os.path.join(self._path, pos_dir))
            self._positions[pds.position_index()] = pds

        if not len(self._positions):
            raise G2SDataError("Micro-manager data set not identified in " + self._path)
        self._name = self._positions[0].name()

    def name(self):
        return self._name

    def num_positions(self):
        return len(self._positions)

    def num_frames(self) -> int:
        return self._positions[0].num_frames()

    def num_channels(self) -> int:
        return self._positions[0].num_channels()

    def num_z_slices(self) -> int:
        return self._positions[0].num_z_slices()

    def width(self):
        return self._positions[0].width()

    def height(self):
        return self._positions[0].height()

    def pixel_type(self):
        return self._positions[0].pixel_type()

    def bit_depth(self):
        return self._positions[0].bit_depth()

    def channel_names(self) -> []:
        return self._positions[0].channel_names()

    def position_labels(self) -> []:
        return [pn.name() for pn in self._positions]

    def pixel_size(self) -> float:
        return self._positions[0].pixel_size()

    def summary_metadata(self) -> dict:
        return self._positions[0].summary_metadata()

    def image_metadata(self, position_index=0, channel_index=0, channel_name="", z_index=0, t_index=0) -> dict:
        return self._positions[position_index].image_metadata(channel_index, channel_name, z_index, t_index)

    def image_pixels(self, position_index=0, channel_index=0, channel_name="", z_index=0, t_index=0) -> np.array:
        return self._positions[position_index].image_pixels(channel_index, channel_name, z_index, t_index)

    def get_position_dataset(self, position_index: int) -> G2SPosDatasetReader:
        return self._positions[position_index]


class G2SPosDatasetWriter:
    # constants
    METADATA_FILE_NAME = 'metadata.txt'
    KEY_SUMMARY = 'Summary'
    KEY_SOURCE = "G2SDataset"

    def __init__(self):
        """ Constructor. Defines an empty data set. """
        self._path = ""
        self._name = ""

        self._z_slices = 0
        self._channel_names = []
        self._frames = 0
        self._positions = 0
        self._width = 0
        self._height = 0
        self._pixel_type = Values.PIX_TYPE_NONE
        self._bit_depth = 0

        self._pixel_size_um = 1.0
        self._summary_meta = {}
        self._meta = {}

    def create(self, root_path: str, name: str, positions=0, channels=0, z_slices=0, frames=0):
        """ Create new data set with specified dimensions"""
        self._path = root_path
        self._name = name

        # create a directory for the dataio
        pos_dir = os.path.join(self._path, self._name)
        if os.path.exists(pos_dir):
            raise G2SDataError("Can't create position directory, one already exists: " + pos_dir)
        os.mkdir(pos_dir)

        self._positions = positions
        self._channel_names = []
        for i in range(channels):
            self._channel_names.append("Channel_" + str(i))
        self._z_slices = z_slices
        self._frames = frames
        self._pixel_size_um = 1.0

    def close(self):
        """ Close data set and write metadata"""
        file_name = os.path.join(self._path, self._name, G2SPosDatasetWriter.METADATA_FILE_NAME)
        with open(file_name, 'w') as fp:
            json_string = json.dumps(self._meta, indent=4)
            fp.write(json_string)

        # this makes writer invalid for further use
        self._meta = None
        self._summary_meta = None
        self._path = None
        self._name = None

    def set_image_dimensions(self, width: int, height: int, pixel_type: Values):
        """Defines image parameters for the entire data set"""
        if self._width != 0 or self._height != 0 or self._pixel_type != Values.PIX_TYPE_NONE:
            raise G2SDataError("Dataset dimensions are already defined")
        self._width = width
        self._height = height
        self._pixel_type = pixel_type

    def set_bit_depth(self, bd: int):
        """
        Sets number of bits per pixel of the useful dynamic range
        If omitted, the bit depth will be equal to number of bits in a pixel
        :param bd: bits per pixel

        """
        self._bit_depth = bd

    def set_pixel_size(self, pixel_size_um: float):
        """
        Sets pixel size in microns, if omitted default is 1.0
        :param pixel_size_um:
        """
        self._pixel_size_um = pixel_size_um

    def set_channel_names(self, channel_names: list):
        """
        Defines channel names, the length must match number of channels defined when data set is created
        :param channel_names: list of channel names as strings
        """
        if len(self._channel_names) == len(channel_names):
            self._channel_names = channel_names
        else:
            raise G2SDataError("Channel names array size does not match existing data")

    def add_image(self, pixels: np.array, position=0, channel=0, z_slice=0, frame=0, additional_meta=None):
        """
        Writes an image with specified coordinates
        :param pixels: nd.array representing image pixels, must match pixel type
        :param position: position coordinate
        :param channel: channel coordinate
        :param z_slice: slice coordinate
        :param frame: frame coordinate
        :param additional_meta: additional image metadata as dictionary
        """
        # determine pixel type
        # TODO: support for FLOAT and RGB64
        if pixels.dtype == np.uint8:
            pixtype = Values.PIX_TYPE_GRAY_8
        elif pixels.dtype == np.uint16:
            pixtype = Values.PIX_TYPE_GRAY_16
        elif pixels.dtype == np.uint32:
            if len(pixels.shape) == 4:
                pixtype = Values.PIX_TYPE_RGB_32
            elif len(pixels.shape) == 2:
                pixtype = Values.PIX_TYPE_GRAY_32
            else:
                raise G2SDataError("Unsupported number of components in np.array type: " + str(pixels.dtype))
        else:
            raise G2SDataError("Unsupported np.array type: " + str(pixels.dtype))

        if self._pixel_type != pixtype:
            raise G2SDataError("Pixel type does not match existing data")

        # image physical dimensions
        w = pixels.shape[0]
        h = pixels.shape[1]

        # check whether image is compatible
        if self._width != w or self._height != h:
            raise G2SDataError("Image dimensions do not match existing data")

        # channel
        if channel not in range(len(self._channel_names)) or \
                z_slice not in range(self._z_slices) or \
                position not in range(self._positions) or \
                frame not in range(self._frames):
            raise G2SDataError("Image coordinates are not valid")

        # set default bit depth if not defined earlier
        if not self._bit_depth:
            if pixels.ndim == 2:
                self._bit_depth = pixels.itemsize * 8
            else:
                self._bit_depth = 8

        if not self._summary_meta:
            self._summary_meta = self._get_summary_meta()
            self._meta[G2SPosDatasetWriter.KEY_SUMMARY] = self._summary_meta

        if additional_meta:
            image_meta = additional_meta
        else:
            image_meta = {}

        image_meta[ImageMeta.WIDTH] = self._width
        image_meta[ImageMeta.HEIGHT] = self._height
        image_meta[ImageMeta.CHANNEL] = channel
        image_meta[ImageMeta.CHANNEL_INDEX] = channel
        image_meta[ImageMeta.CHANNEL_NAME] = self._channel_names[channel]
        image_meta[ImageMeta.POS_INDEX] = position
        image_meta[ImageMeta.FRAME] = frame
        image_meta[ImageMeta.FRAME_INDEX] = frame
        image_meta[ImageMeta.SLICE] = z_slice
        image_meta[ImageMeta.SLICE_INDEX] = z_slice

        image_meta[G2SPosDatasetWriter.KEY_SUMMARY] = self._summary_meta

        self._meta[G2SPosDatasetReader.get_frame_key(channel, z_slice, frame)] = image_meta

        # save image
        file_name = os.path.join(self._path, self._name, ("img_%9d_%s_%d.tif" % (frame, self._channel_names[channel],
                                                                                 z_slice)))
        if not cv2.imwrite(file_name, pixels):
            raise G2SDataError("Image write failed: " + file_name)

    def _get_summary_meta(self):
        summary = {
            SummaryMeta.PREFIX: self._name,
            SummaryMeta.SOURCE: G2SPosDatasetWriter.KEY_SOURCE,
            SummaryMeta.WIDTH: self._width,
            SummaryMeta.HEIGHT: self._height,
            SummaryMeta.PIXEL_TYPE: self._pixel_type,
            SummaryMeta.PIXEL_SIZE: self._pixel_size_um,
            SummaryMeta.BIT_DEPTH: self._bit_depth,
            SummaryMeta.PIXEL_ASPECT: 1,
            SummaryMeta.POSITIONS: self._positions,
            SummaryMeta.CHANNELS: len(self._channel_names),
            SummaryMeta.CHANNEL_NAMES: self._channel_names,
            SummaryMeta.SLICES: self._z_slices,
            SummaryMeta.FRAMES: self._frames
        }
        return summary


class G2SDatasetWriter:

    def __init__(self):
        """ Constructor. Creates an empty data set.
        """
        self._positions = []
        self._root_path = ""
        self._name = ""

    def _empty(self) -> bool:
        return len(self._positions) == 0

    def create(self, root_path: str, name: str):
        self._positions = []
        self._root_path = root_path
        self._name = name
