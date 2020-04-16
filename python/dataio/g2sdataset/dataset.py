# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to support reading micro-manager multi-dimensional
data sets.

"""
import numpy as np


class G2SDataError(Exception):
    pass


VERSION = "1.0.0"


class SummaryMeta:
    """
    Summary metadata represents the entire data set
    Assumed to be set before acquisition starts
    """
    # MANDATORY
    # ---------
    PREFIX = "Prefix"  # serves as a "name"
    SOURCE = "Source"  # source application
    VERSION = "MetadataVersion"
    UUID = "UUID"

    # Multi-D coordinate space (sparse)
    # this represents intended coordinate space limits
    # it is OK if some images are missing
    CHANNELS = "Channels"
    SLICES = "Slices"
    FRAMES = "Frames"
    POSITIONS = "Positions"
    CHANNEL_NAMES = "ChNames"
    CHANNEL_COLORS = "ChColors"

    STAGE_POSITIONS = "StagePositions"

    # image format
    WIDTH = "Width"
    HEIGHT = "Height"
    PIXEL_TYPE = "PixelType"
    PIXEL_SIZE = "PixelSize_um"
    BIT_DEPTH = "BitDepth"
    PIXEL_ASPECT = "PixelAspect"
    NUMBER_OF_COMPONENTS = "NumComponents"

    # acquisition related
    TIME_FIRST = "TimeFirst"
    SLICES_FIRST = "SlicesFirst"
    COMPUTER_NAME = "ComputerName"
    USER_NAME = "UserName"


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


class Image:
    def __init__(self, width=0, height=0, pix_type=Values.PIX_TYPE_NONE):
        if pix_type == Values.PIX_TYPE_NONE:
            self.pixels = None
            self.metadata = {}
        else:
            image_meta = {}
            if pix_type == Values.PIX_TYPE_GRAY_8:
                image_meta[SummaryMeta.PIXEL_TYPE] = Values.PIX_TYPE_GRAY_8
                self.pixels = np.ndarray(shape=(height, width), dtype=np.uint8)
            elif pix_type == Values.PIX_TYPE_GRAY_16:
                image_meta[SummaryMeta.PIXEL_TYPE] = Values.PIX_TYPE_GRAY_16
                self.pixels = np.ndarray(shape=(width, height), dtype=np.uint16)
            elif pix_type == Values.PIX_TYPE_RGB_32:
                image_meta[SummaryMeta.PIXEL_TYPE] = Values.PIX_TYPE_RGB_32
                self.pixels = np.ndarray(shape=(width, height), dtype=np.uint32)
            else:
                raise G2SDataError("Unsupported pixel type: " + pix_type)

            image_meta[ImageMeta.WIDTH] = width
            image_meta[ImageMeta.HEIGHT] = height


class ChannelDef:
    def __init__(self, name="", color=0xFFFFFF):
        self.name = name
        self.color = color


class MCImage:
    def __init__(self):
        self.channel_images = []
        self.channel_defs = []


class Dataset:
    """ Constructs basic data set, without images"""

    def __init__(self, positions=0, channels=1, z_slices=1, frames=1, width=0, height=0, pix_type=Values.PIX_TYPE_NONE):
        self._positions = positions
        self._channels = channels
        self._z_slices = z_slices
        self._frames = frames
        self._width = width
        self._height = height
        self._pix_type = pix_type
        self._pix_size_um = 1.0

        self._images = {}
        self._metadata = {}
        self._channel_defs = []

        # build data structures
        for p in range(positions):
            for c in range(channels):
                self._channel_defs.append(ChannelDef("Channel-%d" % c))
                for z in range(z_slices):
                    for f in range(frames):
                        self._images[self.get_image_key(p, c, z, f)] = Image()

        self._create_basic_meta()

    @classmethod
    def from_metadata(cls, meta: dict) -> object:
        """
        This creates a new dataset based on the summary metadata provided.
        We are assuming that provided metdata has basic information required for construction a valid data set.
        :param meta: summary metadata
        :return: data set, with no images
        """
        ps = meta[SummaryMeta.POSITIONS]
        cs = meta[SummaryMeta.CHANNELS]
        zs = meta[SummaryMeta.SLICES]
        fs = meta[SummaryMeta.FRAMES]
        w = meta[SummaryMeta.WIDTH]
        h = meta[SummaryMeta.HEIGHT]
        pt = meta[SummaryMeta.PIXEL_TYPE]
        ds = Dataset(positions=ps, channels=cs, z_slices=zs, frames=fs, width=w, height=h, pix_type=pt)
        ds._metadata = meta

        # set correct channel names colors based on the metadata
        if SummaryMeta.CHANNEL_NAMES in meta.keys():
            if len(meta[SummaryMeta.CHANNEL_NAMES]) == len(ds._channel_defs):
                for i in range(len(ds._channel_defs)):
                    ds._channel_defs[i].name = meta[SummaryMeta.CHANNEL_NAMES][i]
            else:
                raise Exception("Inconsistent channel names size in the metadata.")

        if SummaryMeta.CHANNEL_COLORS in meta.keys():
            if len(meta[SummaryMeta.CHANNEL_COLORS]) == len(ds._channel_defs):
                for i in range(len(ds._channel_defs)):
                    ds._channel_defs[i].color = meta[SummaryMeta.CHANNEL_COLORS][i]
            else:
                raise Exception("Inconsistent channel colors size in the metadata.")

        if SummaryMeta.PIXEL_SIZE in meta.keys():
            ds._pix_size_um = meta[SummaryMeta.PIXEL_SIZE]

        return ds

    def _create_basic_meta(self):
        """ Utility method to generate metadata from physical data set dimensions"""
        self._metadata[SummaryMeta.POSITIONS] = self._positions
        self._metadata[SummaryMeta.CHANNELS] = self._channels
        self._metadata[SummaryMeta.SLICES] = self._z_slices
        self._metadata[SummaryMeta.FRAMES] = self._frames
        self._metadata[SummaryMeta.WIDTH] = self._width
        self._metadata[SummaryMeta.HEIGHT] = self._height
        self._metadata[SummaryMeta.PIXEL_TYPE] = self._pix_type

        self._metadata[SummaryMeta.CHANNEL_NAMES] = [self._channel_defs[i].name for i in range(len(self._channel_defs))]
        self._metadata[SummaryMeta.CHANNEL_COLORS] = [self._channel_defs[i].color for i in
                                                      range(len(self._channel_defs))]

    @staticmethod
    def get_image_key(position: int, channel: int, z_slice: int, frame: int) -> str:
        """ Returns frame key string based on the three integer coordinates """
        return "ImageKey-%d-%d-%d_%d" % (position, channel, z_slice, frame)

    def set_image_pixels(self, pixels: np.array, position=0, channel=0, z_slice=0, frame=0, meta=None):
        img = Image()
        img.pixels = pixels
        img.metadata = meta
        self._images[self.get_image_key(position, channel, z_slice, frame)] = img

    def set_image(self, img: Image):
        position = img.metadata[ImageMeta.POS_INDEX]
        channel = img.metadata[ImageMeta.CHANNEL_INDEX]
        slice = img.metadata[ImageMeta.SLICE_INDEX]
        frame = img.metadata[ImageMeta.FRAME_INDEX]
        self._images[self.get_image_key(position, channel, slice, frame)] = img

    def get_image(self, position=0, channel=0, z_slice=0, frame=0) -> Image:
        return self._images[self.get_image_key(position, channel, z_slice, frame)]
