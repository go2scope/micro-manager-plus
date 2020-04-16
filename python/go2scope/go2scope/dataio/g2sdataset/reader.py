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

from go2scope.dataio.g2sdataset.dataset import Values, SummaryMeta, G2SDataError, ImageMeta


class PosDatasetReader:
    """ Micro-manager file reader
    
        Represents a multi-dimensional image at a single location.
        Four coordinates: position-frame-channel-slice
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
        self._positions = 0
        self._width = 0
        self._height = 0
        self._pixel_type = Values.PIX_TYPE_NONE
        self._bit_depth = 0

        self._pixel_size_um = 1.0
        self._frame_keys = 4  # default frame key coordinates

        self._metadata = dict()
        self._load_meta()

    def _load_meta(self):
        """ Loads the entire data set, including images
        """

        with open(os.path.join(self._path, PosDatasetReader.METADATA_FILE_NAME)) as md_file:
            # there is a strange bug in some of the micro-manager datasets where closing "}" is
            # missing, so we try to fix
            mdstr = md_file.read()
            try:
                self._metadata = json.loads(mdstr)
            except JSONDecodeError:
                mdstr += '}'
                self._metadata = json.loads(mdstr)

        summary = self._metadata[PosDatasetReader.KEY_SUMMARY]

        if SummaryMeta.PREFIX in summary.keys():
            self._name = summary[SummaryMeta.PREFIX]
        else:
            # figure out the name based on the path
            self._name = os.path.basename(self._path)

        if SummaryMeta.PIXEL_SIZE in summary.keys():
            self._pixel_size_um = summary[SummaryMeta.PIXEL_SIZE]
        self._channel_names = summary[SummaryMeta.CHANNEL_NAMES]
        self._z_slices = summary[SummaryMeta.SLICES]
        self._frames = summary[SummaryMeta.FRAMES]
        self._positions = summary[SummaryMeta.POSITIONS]
        self._width = summary[SummaryMeta.WIDTH]
        self._height = summary[SummaryMeta.HEIGHT]
        self._pixel_type = summary[SummaryMeta.PIXEL_TYPE]
        if SummaryMeta.BIT_DEPTH in summary.keys():
            self._bit_depth = summary[SummaryMeta.BIT_DEPTH]

        for key in self._metadata.keys():
            if key.startswith("FrameKey-"):
                tokens = key.split("-")
                if len(tokens) == 5:
                    self._frame_keys = 4
                    break
                elif len(tokens) == 4:
                    self._frame_keys = 3
                    break
                else:
                    pass

    @staticmethod
    def get_frame_key(position: int, channel: int, z_slice: int, frame: int, num_keys=4) -> str:
        """ Returns frame key string based on the four integer coordinates """
        if num_keys == 4:
            return "FrameKey-%d-%d-%d-%d" % (position, frame, channel, z_slice)
        elif num_keys == 3:
            return "FrameKey-%d-%d-%d" % (frame, channel, z_slice)
        else:
            raise G2SDataError("Invalid number of frame keys: " + num_keys)

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
        Returns position index of the positional sub-dataset.
        This information is stored only in image meta, so we have to search through image metadata
        until we find first one. Search is necessary because particular coordinates are not guaranteed to be available
        """
        for fk in self._metadata.keys():
            if fk.startswith("FrameKey"):
                return int(self._metadata[fk][ImageMeta.POS_INDEX])

        raise G2SDataError("Position index not available in image metadata.")

    def summary_metadata(self) -> dict:
        return self._metadata[PosDatasetReader.KEY_SUMMARY]

    def _get_channel_index(self, cindex: int, cname: str) -> int:
        if cname:
            try:
                return self._channel_names.index(cname)
            except Exception:
                raise G2SDataError("Invalid channel name: " + cname)
        else:
            return cindex

    def image_metadata(self, position_index=0, channel_index=0, z_index=0, t_index=0) -> dict:
        if channel_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or \
                t_index not in range(0, self._frames):
            raise G2SDataError("Invalid image coordinates: channel=%d, slice=%d, frame=%d" % (channel_index, z_index, t_index))

        try:
            md = self._metadata[PosDatasetReader.get_frame_key(position_index, channel_index, z_index, t_index,
                                                               num_keys=self._frame_keys)]
        except Exception as err:
            raise G2SDataError("Frame key not available in metadata: " + err.__str__())

        return md

    def image_pixels(self, position_index=0, channel_index=0, z_index=0, t_index=0) -> np.array:
        if channel_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or \
                t_index not in range(0, self._frames):
            raise G2SDataError("Invalid image coordinates: position=%d, channel=%d, slice=%d, frame=%d" %
                               (position_index, channel_index, z_index, t_index))

        image_path = os.path.join(self._path,
                                  self._metadata[PosDatasetReader.get_frame_key(position_index, channel_index,
                                                                                z_index, t_index,
                                                                                num_keys=self._frame_keys)][ImageMeta.FILE_NAME])
        cv2_image = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
        if cv2_image is None:
            raise G2SDataError("Invalid image reference: " + image_path)
        return cv2_image


class DatasetReader:
    def __init__(self, path: str):
        """ 
        Defines and loads the data set with four coordinates position-channel-slice-frame
        """
        self._positions = []
        self._path = path
        self._name = ""
        self._load_meta()

    def _load_meta(self):
        """ Loads the metadata """
        self._positions = []  # reset contents

        list_of_dirs = [name for name in os.listdir(self._path) if os.path.isdir(os.path.join(self._path, name))]
        self._positions = [None] * len(list_of_dirs)
        for pos_dir in list_of_dirs:
            pds = PosDatasetReader(os.path.join(self._path, pos_dir))
            self._positions[pds.position_index()] = pds

        if not len(self._positions):
            raise G2SDataError("Micro-manager data set not identified in " + self._path)
        self._name = os.path.basename(self._path)

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

    def image_metadata(self, position_index=0, channel_index=0, z_index=0, t_index=0) -> dict:
        return self._positions[position_index].image_metadata(position_index, channel_index, z_index, t_index)

    def image_pixels(self, position_index=0, channel_index=0, z_index=0, t_index=0) -> np.array:
        return self._positions[position_index].image_pixels(position_index, channel_index, z_index, t_index)

    def get_position_name(self, p):
        return self._positions[p].name()

