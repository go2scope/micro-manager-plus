# -*- coding: utf-8 -*-
""" Go2Scope data set

Module to suppord reading go2scope (micro-manager) multi-dimensional
data sets.

"""

import json
import cv2
from datasetOpenCV import g2simage
import os
from shutil import copyfile


class DatasetInfo:
    """ datasetOpenCV information """

    def __init__(self):
        self.frames = dict()
        self.comment = ""

        self.zslices = 0
        self.channel_names = []
        self.channels = 0
        self.timepoints = 0

        self.pixel_size_um = 1.0


class G2SDataset:
    """ go2scope datasetOpenCV
    
        Represents a multi-dimensional image. In this version supports
        three coordinates: channels, z-slices and timepoints.
        
    """

    # constants
    METADATA_FILE_NAME = 'metadata.txt'
    COMMENTS_FILE_NAME = 'display_and_comments.txt'
    KEY_SUMMARY = 'Summary'
    KEY_PIXEL_SIZE = "PixelSize_um"
    KEY_CHANNEL_NAMES = "ChNames"
    KEY_SLICES = "Slices"
    KEY_FRAMES = "Frames"
    KEY_CHANNELS = "Channels"
    KEY_ZPOS = "ZPositionUm"
    KEY_FILENAME = "FileName"
    KEY_WIDTH = "Width"
    KEY_HEIGHT = "Height"
    KEY_COMMENTS = "Comments"


    def __init__(self):
        """ Constructor. Defines an empty data set. """
        self._path = ""
        self._frames = dict()
        self._comment = ""  # not populated for now

        self._zslices = 0
        self._channel_names = []
        self._timepoints = 0

        self._pixel_size_um = 1.0

    def load(self, dir_path, scale=1.0):
        """ Loads the entire data set, including images
            
            Args:
                dir_path (str): datasetOpenCV directory path
                scale (float): scaling factor for images, default 1.0
        """

        self._path = dir_path
        with open(self._path + '/' + G2SDataset.METADATA_FILE_NAME) as md_file:
            md = json.load(md_file)

        with open(self._path + '/' + G2SDataset.COMMENTS_FILE_NAME) as comments_file:
            comments_md = json.load(comments_file)

        summary = md[G2SDataset.KEY_SUMMARY]
        self._pixel_size_um = summary[G2SDataset.KEY_PIXEL_SIZE]
        self._channel_names = summary[G2SDataset.KEY_CHANNEL_NAMES]
        self._zslices = summary[G2SDataset.KEY_SLICES]
        self._timepoints = summary[G2SDataset.KEY_FRAMES]
        self._comment = comments_md[G2SDataset.KEY_COMMENTS][G2SDataset.KEY_SUMMARY]

        # parse image frames
        for key, subdict in md.items():
            if key != G2SDataset.KEY_SUMMARY:
                z = subdict[G2SDataset.KEY_ZPOS]
                fname = self._path + '/' + subdict[G2SDataset.KEY_FILENAME]
                cv2_image = cv2.imread(fname, -1)
                if scale < 1.0:
                    # reduce image size
                    img = g2simage.G2SImage(cv2.resize(cv2_image, None, fx=float(scale), fy=float(scale),
                                                       interpolation=cv2.INTER_CUBIC), z)
                else:
                    img = g2simage.G2SImage(cv2_image, z)

                self._frames[key] = img

    @staticmethod
    def __frame_key(channel, zslice, timepoint):
        """ Returns frame key string based on the three integer coordinates """
        return "FrameKey" + "-" + str(timepoint) + "-" + str(channel) + "-" + str(zslice);

    @staticmethod
    def get_info(dir_path):
        """ Utility function that returns basic datasetOpenCV information
            without loading images. Might be useful for quickly scanning
            multiple data sets.
            
            Args:
                dir_path (str): datasetOpenCV directory path
                
            Returns:
                DatasetInfo: basic information
        """
        with open(dir_path + '/' + G2SDataset.METADATA_FILE_NAME) as md_file:
            md = json.load(md_file)

        summary = md[G2SDataset.KEY_SUMMARY]
        dsinf = DatasetInfo()
        dsinf.pixelSizeUm = summary[G2SDataset.KEY_PIXEL_SIZE]
        dsinf.channels = summary[G2SDataset.KEY_CHANNELS]
        dsinf.zslices = summary[G2SDataset.KEY_SLICES]
        dsinf.timepoints = summary[G2SDataset.KEY_FRAMES]
        dsinf.channel_names = summary[G2SDataset.KEY_CHANNEL_NAMES]
        return dsinf

    @staticmethod
    def rescale(source, target, scale):
        """ Rescale entire data set with correct metadata """
        # create target directory
        os.makedirs(target)

        # copy metadata
        copyfile(source + '/' + G2SDataset.METADATA_FILE_NAME, target + '/' + G2SDataset.METADATA_FILE_NAME)
        copyfile(source + '/' + G2SDataset.COMMENTS_FILE_NAME, target + '/' + G2SDataset.COMMENTS_FILE_NAME)

        # iterate on tif files, scale them and save to target
        list_source = os.listdir(source)
        newx = 0
        newy = 0
        for f in list_source:
            if f.startswith('img_'):
                imsrc = cv2.imread(source + '/' + f, -1)
                imdest = cv2.resize(imsrc, None, fx=float(scale), fy=float(scale), interpolation=cv2.INTER_CUBIC)
                cv2.imwrite(target + '/' + f, imdest)
                newx = imdest.shape[0]
                newy = imdest.shape[1]

        # now fix metadata
        md_file_name = target + '/' + G2SDataset.METADATA_FILE_NAME
        md_file = open(md_file_name)
        md = json.load(md_file)
        md_file.close()
        md[G2SDataset.KEY_SUMMARY][G2SDataset.KEY_WIDTH] = newx
        md[G2SDataset.KEY_SUMMARY][G2SDataset.KEY_HEIGHT] = newy

        # fix metadata for image frames
        for key, subdict in md.items():
            if key != G2SDataset.KEY_SUMMARY:
                subdict[G2SDataset.KEY_WIDTH] = newx
                subdict[G2SDataset.KEY_HEIGHT] = newy
                frame_summary = subdict[G2SDataset.KEY_SUMMARY]
                frame_summary[G2SDataset.KEY_WIDTH] = newx
                frame_summary[G2SDataset.KEY_HEIGHT] = newy

        # clear old file
        os.remove(md_file_name)

        # write new one
        md_file = open(md_file_name, 'w')
        json.dump(md, md_file, indent=4)
        md_file.close()

    def image(self, channel, zslice, timepoint):
        """ Returns cv2 image at given coordinates.
        
            Args:
                channel (int): channel index
                zslice (int): slice index
                timepoint (int): time index
        
        """

        frkey = self.__frame_key(channel, zslice, timepoint)
        return self._frames[frkey]

    def num_frames(self):
        return self._timepoints

    def num_channels(self):
        return len(self._channel_names)

    def num_zslices(self):
        return self._zslices

    def channel_names(self):
        return self._channel_names

    def pixel_size(self):
        return self._pixel_size_um
