import json
from json import JSONDecodeError
import cv2
import numpy as np

from dataio.g2sdataset.reader import PosDatasetReader, DatasetReader
from dataio.g2sdataset.dataset import SummaryMeta
from dataio.g2sdataset.dataset import G2SDataError
from dataio.g2sdataset.dataset import ImageMeta
from awslp.awslp import S3Bucket


class S3DatasetReader(DatasetReader):

    def __init__(self,
                 path: str,
                 s3_bucket_name: str,
                 region_name: str,
                 access_key_id: str,
                 secret_key: str,
                 session_token: str) -> None:
        """ Constructor.
        :param path: path to dataset on S3
        :param s3_bucket_name:
        :param region_name:
        :param access_key_id:
        :param secret_key:
        :param session_token:
        """
        self._connect_to_s3(s3_bucket_name, region_name, access_key_id, secret_key, session_token)
        super().__init__(path)

    def _connect_to_s3(self,
                       s3_bucket_name: str,
                       region_name: str,
                       access_key_id: str,
                       secret_key: str,
                       session_token: str) -> None:
        """ Connect to S3 bucket.
        :param s3_bucket_name:
        :param region_name:
        :param access_key_id:
        :param secret_key:
        :param session_token:
        """
        self._s3_bucket = S3Bucket(s3_bucket_name,
                                   region_name,
                                   access_key_id,
                                   secret_key,
                                   session_token)

    def _load_meta(self) -> None:
        """ Loads the metadata from S3.
        """
        self._positions = []  # reset contents

        list_of_dirs, _, _ = self._s3_bucket.get_all_objects(self._path)
        list_of_dirs = [e.replace(self._path + '/', '').split('/')[0] for e in list_of_dirs]
        list_of_dirs = set(list_of_dirs)
        # TODO check allowed extensions
        list_of_dirs = [e for e in list_of_dirs if not (e.endswith('.txt') or
                                                        e.endswith('.png') or
                                                        e.endswith('.tif') or
                                                        e.endswith('.jpeg') or e == '')]
        self._positions = [None] * len(list_of_dirs)
        for pos_dir in list_of_dirs:
            pds = G2SPosDatasetReaderS3(self._path + '/' + pos_dir, self._s3_bucket)
            self._positions[pds.position_index()] = pds

        if not len(self._positions):
            raise G2SDataError("Micro-manager data set not identified in " + self._path)
        self._name = self._positions[0].name()


class G2SPosDatasetReaderS3(PosDatasetReader):

    def __init__(self, path: str, s3_bucket: S3Bucket) -> None:
        """ Constructor.
        :param path: path to Pos data
        :param s3_bucket: S3 Bucket object
        """
        self._s3_bucket = s3_bucket
        super().__init__(path)

    def _load_meta(self) -> None:
        """ Loads the entire data set, including images
        """
        md_str = self._s3_bucket.get_file_content(self._path + '/' + PosDatasetReader.METADATA_FILE_NAME)
        # there is a strange bug in some of the micro-manager datasets where closing "}" is
        # missing, so we try to fix
        try:
            self._metadata = json.loads(md_str)
        except JSONDecodeError:
            md_str += '}'
            self._metadata = json.loads(md_str)
        summary = self._metadata[PosDatasetReader.KEY_SUMMARY]

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

    def image_pixels(self, channel_index: int=0, channel_name: str="", z_index: int=0, t_index: int=0) -> np.array:
        """ Get image pixels received from S3.
        :param channel_index:
        :param channel_name:
        :param z_index:
        :param t_index:
        :return: image pixels matrix
        """
        ch_index = self._get_channel_index(channel_index, channel_name)
        if ch_index not in range(len(self._channel_names)) or z_index not in range(self._z_slices) or \
                t_index not in range(0, self._frames):
            raise G2SDataError("Invalid image coordinates: channel=%d, slice=%d, frame=%d" % (ch_index, z_index, t_index))

        image_path = self._path + '/' + self._metadata[PosDatasetReader.get_frame_key(channel_index, z_index, t_index)][ImageMeta.FILE_NAME]
        data = self._s3_bucket.get_file_object(image_path)
        image_pixel_type = self.pixel_type()

        # TODO support missing types
        pixel_type = dict()
        pixel_type['GRAY8'] = np.uint8
        pixel_type['GRAY16'] = np.uint16
        pixel_type['RGB16'] = np.uint8
        pixel_type['RGB32'] = np.uint16

        file_stream = np.fromstring(data, pixel_type[image_pixel_type])
        cv2_image = cv2.imdecode(file_stream, cv2.IMREAD_UNCHANGED)
        if cv2_image is None:
            raise G2SDataError("Invalid image reference: " + image_path)
        return cv2_image
