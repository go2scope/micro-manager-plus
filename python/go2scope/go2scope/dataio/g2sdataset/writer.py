# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to support reading micro-manager multi-dimensional
data sets.

"""
import datetime
import getpass
import json
import os
import shutil
import socket
import uuid

import cv2
# import imageio
# TODO switch from cv2 to imageio and write image metadata in the TIF file

import numpy as np

from go2scope.dataio.g2sdataset.dataset import Values, G2SDataError, ImageMeta, SummaryMeta, ChannelDef
from go2scope.dataio.g2sdataset.reader import PosDatasetReader


class PosDatasetWriter:
    """
    Micro-manager file format writer for a single position
    Intended for use only incorporated in the DatasetWriter
    """
    # constants
    ERRMSG_META_FROZEN = "We can't change the parameter, summary metadata is already frozen"
    METADATA_FILE_NAME = 'metadata.txt'
    KEY_SUMMARY = 'Summary'
    KEY_SOURCE = "G2SDataset"

    def __init__(self):
        """ Constructor. Defines an empty data set. """
        self._path = ""
        self._name = ""

        self._z_slices = 0
        self._channel_defs = []
        self._frames = 0
        self._positions = 0
        self._width = 0
        self._height = 0
        self._pixel_type = Values.PIX_TYPE_NONE
        self._num_components = 1
        self._bit_depth = 0

        self._pixel_size_um = 1.0
        self._meta = {}
        self._additional_summary_meta = {}

        self._time_first = True  # TODO: elaborate on this
        self._slices_first = False

        self._uuid = str(uuid.uuid1())
        self._computer_name = socket.gethostname()
        self._user_name = getpass.getuser()
        self._images_saved = False  # flags if there are any images saved for this position

        self._meta_version = 9
        # this is important to be less than 10, because we don't know how to insert
        # metadata in the TIFF Info field

    def open(self, root_path: str, name: str, positions=0, channels=0, z_slices=0, frames=0, additional_meta=None):
        """ Create new data set with specified dimensions"""
        if additional_meta is None:
            additional_meta = {}
        self._path = root_path
        self._name = name
        if additional_meta:
            self._additional_summary_meta = additional_meta

        self._positions = positions
        self._channel_defs = []
        for i in range(channels):
            self._channel_defs.append(ChannelDef("Channel-" + str(i)))
        self._z_slices = z_slices
        self._frames = frames
        self._pixel_size_um = 1.0
        self._images_saved = False

    def initialize(self, width: int, height: int, pixel_type: Values, bit_depth: int, num_components=1):
        """Defines image parameters for the entire data set"""
        if self._width != 0 or self._height != 0 or self._pixel_type != Values.PIX_TYPE_NONE:
            raise G2SDataError("Dataset dimensions are already defined")
        self._width = width
        self._height = height
        self._pixel_type = pixel_type
        self._bit_depth = bit_depth
        self._num_components = num_components

    def close(self):
        """ Close data set and write metadata"""
        self.save_metadata()

        # this makes writer invalid for further use
        self._meta = None
        self._summary_meta = None
        self._path = None
        self._name = None

    def name(self):
        return self._name

    def set_name(self, name: str):
        if not self._empty():
            raise G2SDataError(PosDatasetWriter.ERRMSG_META_FROZEN)
        self._name = name

    def save_metadata(self):
        """ Saves metadata. This can be used to occasionally save metadata to disk"""
        # create a directory for the data
        pos_dir = os.path.join(self._path, self._name)
        if not os.path.exists(pos_dir):
            os.mkdir(pos_dir)

        # we are signaling that we can't change position names anymore because directory name is frozen
        self._images_saved = True

        file_name = os.path.join(pos_dir, PosDatasetWriter.METADATA_FILE_NAME)
        with open(file_name, 'w') as fp:
            json_string = json.dumps(self._meta, indent=4)
            fp.write(json_string)

    def set_pixel_size(self, pixel_size_um: float):
        """
        Sets pixel size in microns, if omitted default is 1.0
        :param pixel_size_um:
        """
        if not self._empty():
            raise G2SDataError(PosDatasetWriter.ERRMSG_META_FROZEN)
        self._pixel_size_um = pixel_size_um

    def set_channel_data(self, channel_data: list):
        """
        Defines channel names, the length must match number of channels defined when data set is created
        :param channel_data: list of channel definitions
        """
        if not self._empty():
            raise G2SDataError(PosDatasetWriter.ERRMSG_META_FROZEN)

        if len(self._channel_defs) == len(channel_data):
            self._channel_defs = channel_data
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
        self._num_components = 1
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
        h = pixels.shape[0]
        w = pixels.shape[1]

        # check whether image is compatible
        if self._width != w or self._height != h:
            raise G2SDataError("Image dimensions do not match existing data")

        # channel
        if channel not in range(len(self._channel_defs)) or \
                z_slice not in range(self._z_slices) or \
                position not in range(self._positions) or \
                frame not in range(self._frames):
            raise G2SDataError("Image coordinates are not valid")

        if self._empty():
            self._meta[PosDatasetWriter.KEY_SUMMARY] = self._create_summary_meta()

        image_meta = {}
        if additional_meta:
            image_meta.update(additional_meta)

        image_meta[ImageMeta.WIDTH] = self._width
        image_meta[ImageMeta.HEIGHT] = self._height
        image_meta[ImageMeta.CHANNEL] = channel
        image_meta[ImageMeta.CHANNEL_INDEX] = channel
        image_meta[ImageMeta.CHANNEL_NAME] = self._channel_defs[channel].name
        image_meta[ImageMeta.POS_INDEX] = position
        image_meta[ImageMeta.FRAME] = frame
        image_meta[ImageMeta.FRAME_INDEX] = frame
        image_meta[ImageMeta.SLICE] = z_slice
        image_meta[ImageMeta.SLICE_INDEX] = z_slice
        image_meta[SummaryMeta.PIXEL_TYPE] = self._pixel_type
        image_meta[SummaryMeta.PIXEL_SIZE] = self._pixel_size_um
        image_meta[SummaryMeta.BIT_DEPTH] = self._bit_depth
        if SummaryMeta.UUID not in image_meta:
            image_meta[SummaryMeta.UUID] = str(uuid.uuid1())
        image_meta[ImageMeta.POS_NAME] = self._name

        file_name = "img_%09d_%s_%03d.tif" % (frame, self._channel_defs[channel].name, z_slice)
        image_meta[ImageMeta.FILE_NAME] = file_name

        # we are not inserting summary data anymore
        # image_meta[PosDatasetWriter.KEY_SUMMARY] = self._summary_meta

        self._meta[PosDatasetReader.get_frame_key(position, channel, z_slice, frame)] = image_meta

        # save image
        pos_dir = os.path.join(self._path, self._name)
        if not os.path.exists(pos_dir):
            os.mkdir(pos_dir)

        file_name = os.path.join(pos_dir, file_name)
        if not cv2.imwrite(file_name, pixels):
            raise G2SDataError("Image write failed: " + file_name)

        self._images_saved = True  # signals that some image files already exist on disk

        # TODO
        # wr = imageio.get_writer(file_name)
        # wr.append_data(pixels, meta={"description": json.dumps(image_meta, indent=4)})
        # wr.close()

    def _create_summary_meta(self) -> dict:
        """ Utility function to create essential summary metdata """
        summary = {}
        summary.update(self._additional_summary_meta)  # add additional summary info
        summary[SummaryMeta.PREFIX] = self._name
        summary[SummaryMeta.SOURCE] = PosDatasetWriter.KEY_SOURCE
        summary[SummaryMeta.WIDTH] = self._width
        summary[SummaryMeta.HEIGHT] = self._height
        summary[SummaryMeta.PIXEL_TYPE] = self._pixel_type
        summary[SummaryMeta.PIXEL_SIZE] = self._pixel_size_um
        summary[SummaryMeta.BIT_DEPTH] = self._bit_depth
        summary[SummaryMeta.PIXEL_ASPECT] = 1
        summary[SummaryMeta.POSITIONS] = self._positions
        summary[SummaryMeta.CHANNELS] = len(self._channel_defs)
        summary[SummaryMeta.CHANNEL_NAMES] = [cd.name for cd in self._channel_defs]
        summary[SummaryMeta.CHANNEL_COLORS] = [cd.color for cd in self._channel_defs]
        summary[SummaryMeta.SLICES] = self._z_slices
        summary[SummaryMeta.FRAMES] = self._frames
        summary[SummaryMeta.TIME_FIRST] = self._time_first
        summary[SummaryMeta.SLICES_FIRST] = self._slices_first
        summary[SummaryMeta.NUMBER_OF_COMPONENTS] = self._num_components
        summary[SummaryMeta.UUID] = self._uuid
        summary[SummaryMeta.VERSION] = self._meta_version
        summary[SummaryMeta.COMPUTER_NAME] = self._computer_name
        summary[SummaryMeta.USER_NAME] = self._user_name
        summary[SummaryMeta.TIME] = datetime.datetime.now()

        return summary

    def _empty(self):
        return not self._images_saved


class DatasetWriter:
    """
    Write 6-D datasets in micro-manager 'classic' format
    """

    def __init__(self):
        """ Constructor. Creates an empty data set.
        """
        self._number_of_components = 1
        self._positions = []
        self._root_path = ""
        self._name = ""
        self._channel_defs = []
        self._positions = []
        self._z_slices = 0
        self._frames = 0
        self._additional_summary_meta = {}

        self._pixel_type = Values.PIX_TYPE_NONE
        self._width = 0
        self._height = 0
        self._bit_depth = 0
        self._pix_size_um = 1.0

        self._comment = ""

    def _empty(self) -> bool:
        return len(self._positions) == 0

    def open(self, root_path: str, name: str, positions=1, channels=1, z_slices=1, frames=1, overwrite=False,
             additional_meta=None):
        """
        Create new data set
        :param positions: number of positions
        :param channels:  number of channels
        :param z_slices: number of z steps
        :param frames: number of time points
        :param additional_meta: additional summary metadata
        :param root_path: parent directory for the dataset
        :param name: data set name, folder name
        :param overwrite: deletes existing datasets with the same name
        :return: none
        """
        self._positions = [None] * positions
        self._root_path = root_path
        self._name = name
        self._channel_defs = []
        for c in range(channels):
            self._channel_defs.append(ChannelDef("Channel-%d" % c))
        self._z_slices = z_slices
        self._frames = frames
        self._additional_summary_meta = {}
        if additional_meta:
            self._additional_summary_meta = additional_meta

        ds_dir = os.path.join(root_path, name)
        if overwrite:
            # we are instructed to overwrite existing datasets in the same path
            if os.path.exists(ds_dir):
                # before deleting data we do a few checks to make sure we are overwriting another dataset
                # if it doesn't look like a dataset, we refuse to overwrite
                if not os.path.isdir(ds_dir):
                    raise G2SDataError("We can't overwrite non-directory path: " + ds_dir)
                list_of_dirs = [name for name in os.listdir(ds_dir)]
                if not len(list_of_dirs):
                    raise G2SDataError("Doesn't look like dataset path so we can't overwrite: " + ds_dir)
                metadata_path = os.path.join(ds_dir, list_of_dirs[0], "metadata.txt")
                if not os.path.exists(metadata_path):
                    raise G2SDataError("Can't find metadata.txt, so we can't overwrite: " + ds_dir)

                # this dumps the entire tree
                shutil.rmtree(ds_dir, ignore_errors=True)
        else:
            if os.path.exists(ds_dir):
                raise G2SDataError("Directory already exists: " + ds_dir)

        os.mkdir(ds_dir)  # create directory for the data set

    def initialize(self, width: int, height: int, pixel_type: Values, bit_depth=0):
        """Defines image parameters for the entire data set
        :param width: image width in pixels
        :param height: image height in pixels
        :param pixel_type: pixel type
        :param bit_depth: dynamic range in bits, if 0 maximum range will be used for a given pixel type
        """
        if self._width != 0 or self._height != 0 or self._pixel_type != Values.PIX_TYPE_NONE:
            raise G2SDataError("Dataset dimensions are already defined")
        self._width = width
        self._height = height
        self._pixel_type = pixel_type
        self._bit_depth = bit_depth
        self._number_of_components = 1

        # set default bit depth if not specified
        if not self._bit_depth:
            if self._pixel_type == Values.PIX_TYPE_GRAY_8:
                self._bit_depth = 8
            elif self._pixel_type == Values.PIX_TYPE_GRAY_16:
                self._bit_depth = 16
            elif self._pixel_type == Values.PIX_TYPE_RGB_32:
                self._bit_depth = 256
                self._number_of_components = 4
            elif self._pixel_type == Values.PIX_TYPE_RGB_64:
                self._bit_depth = 16
                self._number_of_components = 4
            elif self._pixel_type == Values.PIX_TYPE_GRAY_32:
                self._bit_depth = 32
            else:
                raise G2SDataError("Unsupported pixel type: " + str(pixel_type))

        # create an array of empty positional data sets
        for p in range(len(self._positions)):
            self._positions[p] = PosDatasetWriter()
            pos_name = "Pos-" + str(p)
            root_dir = os.path.join(self._root_path, self._name)
            self._positions[p].open(root_dir, pos_name, len(self._positions),
                                    len(self._channel_defs),
                                    self._z_slices, self._frames, additional_meta=self._additional_summary_meta)

            self._positions[p].initialize(self._width, self._height, self._pixel_type, self._bit_depth,
                                          num_components=self._number_of_components)
            self._positions[p].set_channel_data(self._channel_defs)
            self._positions[p].set_pixel_size(self._pix_size_um)

    def set_channel_data(self, channel_data: list):
        """
        Defines channel names, the length must match number of channels defined when data set is created
        :param channel_data: list of channel definitions
        """
        if len(self._channel_defs) == len(channel_data):
            self._channel_defs = channel_data
        else:
            raise G2SDataError("Channel names array size does not match existing data")

    def set_position_name(self, p: int, name: str):
        """ Changes the default name of the position """
        self._positions[p].set_name(name)

    def set_pixel_size(self, pixel_size_um: float):
        """
        Sets pixel size in microns, if omitted default is 1.0
        :param pixel_size_um:
        """
        self._pix_size_um = pixel_size_um

    def set_comment(self, text: str):
        self._comment = text

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

        self._positions[position].add_image(pixels, position=position, channel=channel, z_slice=z_slice, frame=frame,
                                            additional_meta=additional_meta)

    def close(self):
        """ closes entire data set and saves all metadata """
        for pos in self._positions:
            if pos:
                pos.close()

        # TODO: save comments to comment file

        # this makes writer invalid for further use
        self._root_path = None
        self._name = None

    def save_metadata(self):
        """ Saves current metadata """
        for pos in self._positions:
            if pos:
                pos.save_metadata()
