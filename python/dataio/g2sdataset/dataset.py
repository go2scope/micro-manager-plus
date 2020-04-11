# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to support reading micro-manager multi-dimensional
data sets.

"""


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
