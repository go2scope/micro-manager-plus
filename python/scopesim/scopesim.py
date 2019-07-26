"""
Microscope Simulator: ScopeSim

Simulates a microscope equipped with a camera, focus stage and filter changer

"""
import numpy
import cv2


from datasetOpenCV import g2sdataset
from datasetOpenCV import g2simage

import logging


class ScopeSim:

    STAGE_PRECISION = 0.01

    def __init__(self):
        self._current_image = None
        self._current_channel = None
        self._channels = []
        self._dataset = None
        self._z_range = (0.0, 0.0)
        self._current_z = 0.0

    def init(self, dataset_path, scale=1.0):
        self._dataset = g2sdataset.G2SDataset()
        self._dataset.load(dataset_path, scale)
        self._channels = self._dataset.channel_names()
        self._current_channel = 0

        # establish range of focus positions
        self._z_range = (float(self._dataset.image(self._current_channel, 0, 0).z),
                         float(self._dataset.image(self._current_channel, self._dataset.num_zslices() - 1, 0).z))

        # by default position on the first slice
        self._current_image = self._dataset.image(self._current_channel, 0, 0)
        self._current_z = float(self._z_range[0])

    def z_range(self):
        return self._z_range

    def get_image(self):
        """ returns current image at current z position and current channel """
        return self._current_image

    def get_channel_name(self):
        return self._channels[self._current_channel]

    def get_channel(self):
        return self._current_channel

    def get_channels(self):
        return self._channels

    def set_channel(self, channel):
        """ sets channel
            this operation triggers image generation
        """
        self._current_channel = channel
        self.__generate_image()

    def set_z(self, z):
        """ sets z stage position
            this operation triggers image generation
        """
        self._current_z = z
        self.__generate_image()

    @staticmethod
    def __blend_images(img1, img2, z):
        """ blend two images based on the z value
            assuming that img1.z < z <= img2.z
            blending formula: img1*alpha + img2*beta + gamma

            Returns:
                G2SImage: blended image
        """
        delta = img2.z - img1.z
        alpha = 1.0 - (z - img1.z) / delta
        beta = 1.0 - (img2.z - z) / delta
        gamma = 0.0
        img_blended = numpy.zeros((img1.pixels.shape[1], img1.pixels.shape[0], 1), numpy.uint16)
        cv2.addWeighted(img1.pixels, alpha, img2.pixels, beta, gamma, img_blended)
        # print("Blended images z=%f, alpha=%f and z=%f, beta=%f " % (img1.z, alpha, img2.z, beta))
        return g2simage.G2SImage(img_blended, z)

    def __generate_image(self):
        """ For a given _current_Z and _current_channel find the closest two neighbors
            in the z-stack. If the distance between current_z and closest slice is less
            than mechanical tolerance of the stage, return the closest slice image as is.
            If not, then interpolate between two nearest neighbors using linear interpolation.

        """
        # naive linear search to find closest image
        # assumes that images are monotonously increasing z
        # TODO: replace with more efficient
        try:
            for i in range(1, self._dataset.num_zslices()):
                img = self._dataset.image(self._current_channel, i, 0)
                img_prev = self._dataset.image(self._current_channel, i-1, 0)
                if img.z >= self._current_z:
                    # print("Found slice " + str(i) + ", z=" + str(img.z) + ", current_z=" + str(self._current_z))
                    if abs(img.z - self._current_z) < ScopeSim.STAGE_PRECISION:
                        # within stage tolerance so we can return
                        # the actual image
                        self._current_image = img
                        return
                    elif abs(img_prev.z - self._current_z) < ScopeSim.STAGE_PRECISION:
                        self._current_image = img_prev
                        return
                    else:
                        # we are outside stage tolerance so we have to interpolate
                        # and blend two nearest images
                        self._current_image = ScopeSim.__blend_images(img_prev, img, self._current_z)
                        return

            # we get to this point if we did not find a matching image,
            self._current_image = None
            raise Exception('Z range exceeded. Z:', self._current_z)
        except:
            logging.exception("GENERATE IMAGE")