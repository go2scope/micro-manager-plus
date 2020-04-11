# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to support reading micro-manager multi-dimensional
data sets.

"""
import json
import os
import shutil

import cv2
import numpy as np

from dataio.g2sdataset.dataset import Values, G2SDataError, ImageMeta, SummaryMeta
from dataio.g2sdataset.reader import PosDatasetReader


class PosDatasetWriter:
    """
    Micro-manager file format writer
    """
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
        self._additional_summary_meta = {}

    def create(self, root_path: str, name: str, positions=0, channels=0, z_slices=0, frames=0, additional_meta=None):
        """ Create new data set with specified dimensions"""
        if additional_meta is None:
            additional_meta = {}
        self._path = root_path
        self._name = name
        if additional_meta:
            self._additional_summary_meta = additional_meta

        # create a directory for the data
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
        self.save_metadata()

        # this makes writer invalid for further use
        self._meta = None
        self._summary_meta = None
        self._path = None
        self._name = None

    def save_metadata(self):
        """ Saves metadata. This can be used to occasionally save metadata to disk"""
        file_name = os.path.join(self._path, self._name, PosDatasetWriter.METADATA_FILE_NAME)
        with open(file_name, 'w') as fp:
            json_string = json.dumps(self._meta, indent=4)
            fp.write(json_string)

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
            self._summary_meta = self._create_summary_meta()
            self._meta[PosDatasetWriter.KEY_SUMMARY] = self._summary_meta

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

        image_meta[PosDatasetWriter.KEY_SUMMARY] = self._summary_meta

        self._meta[PosDatasetReader.get_frame_key(channel, z_slice, frame)] = image_meta

        # save image
        file_name = os.path.join(self._path, self._name, ("img_%9d_%s_%d.tif" % (frame, self._channel_names[channel],
                                                                                 z_slice)))
        if not cv2.imwrite(file_name, pixels):
            raise G2SDataError("Image write failed: " + file_name)

    def _create_summary_meta(self):
        summary = self._additional_summary_meta
        summary[SummaryMeta.PREFIX] = self._name
        summary[SummaryMeta.SOURCE] = PosDatasetWriter.KEY_SOURCE
        summary[SummaryMeta.WIDTH] = self._width
        summary[SummaryMeta.HEIGHT] = self._height
        summary[SummaryMeta.PIXEL_TYPE] = self._pixel_type
        summary[SummaryMeta.PIXEL_SIZE] = self._pixel_size_um
        summary[SummaryMeta.BIT_DEPTH] = self._bit_depth
        summary[SummaryMeta.PIXEL_ASPECT] = 1
        summary[SummaryMeta.POSITIONS] = self._positions
        summary[SummaryMeta.CHANNELS] = len(self._channel_names)
        summary[SummaryMeta.CHANNEL_NAMES] = self._channel_names
        summary[SummaryMeta.SLICES] = self._z_slices
        summary[SummaryMeta.FRAMES] = self._frames

        return summary


class DatasetWriter:

    def __init__(self):
        """ Constructor. Creates an empty data set.
        """
        self._positions = []
        self._root_path = ""
        self._name = ""
        self._channels = 0
        self._positions = []
        self._z_slices = 0
        self._frames = 0
        self._additional_summary_meta = {}

    def _empty(self) -> bool:
        return len(self._positions) == 0

    def create(self, root_path: str, name: str, positions=1, channels=1, z_slices=1, frames=1, overwrite=False,
               additional_meta=None):
        """
        Create new data set
        :param root_path:
        :param name:
        :param overwrite: deletes existing datasets with the same name
        :return:
        """
        self._positions = [None] * positions
        self._root_path = root_path
        self._name = name
        self._channels = channels
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
                if os.path.exists(os.path.join(ds_dir, list_of_dirs[0], "metadata.txt")):
                    raise G2SDataError("Can't find metadata.txt, so we can't overwrite: " + ds_dir)

                # this dumps the entire tree
                shutil.rmtree(ds_dir, ignore_errors=True)
        else:
            if os.path.exists(ds_dir):
                raise G2SDataError("Directory already exists: " + ds_dir)

        os.mkdir(ds_dir)  # create directory for the data set

    def add_image(self, pixels: np.array, position=0, position_name="", channel=0, z_slice=0, frame=0,
                  additional_meta=None):
        """
        Writes an image with specified coordinates
        :param position_name: name of the position
        :param pixels: nd.array representing image pixels, must match pixel type
        :param position: position coordinate
        :param channel: channel coordinate
        :param z_slice: slice coordinate
        :param frame: frame coordinate
        :param additional_meta: additional image metadata as dictionary
        """
        if not self._positions[position]:
            # create a positional data set
            pos_ds = PosDatasetWriter()
            pos_name = "Pos_" + str(position)
            if position_name:
                pos_name = position_name

            pos_ds.create(os.path.join(self._root_path, self._name), pos_name, len(self._positions), self._channels,
                          self._z_slices, self._frames)
            self._positions[position] = pos_ds
        else:
            pos_ds = self._positions[position]
            if position_name:
                if pos_ds.name() != position_name:
                    raise G2SDataError("Position name does not mach existing one: " + position_name)

        # finally add image
        pos_ds.add_image(pixels, position=position, channel=channel, z_slice=z_slice, frame=frame,
                         additional_meta=additional_meta)

    def close(self):
        """ closes entire data set and saves all metadata """
        for pos in self._positions:
            if pos:
                pos.close()

        # this makes writer invalid for further use
        self._root_path = None
        self._name = None
