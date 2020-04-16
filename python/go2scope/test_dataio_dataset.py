import argparse
# parse command line arguments
import json
import os

import numpy as np

from go2scope.dataio.g2sdataset.dataset import ChannelDef, Values, ImageMeta, G2SDataError
from go2scope.dataio.g2sdataset.reader import DatasetReader
from go2scope.dataio.g2sdataset.writer import DatasetWriter

parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path for the generated dataset')
args = parser.parse_args()

ds_name = "WriteTest"

# imaging parameters
num_positions = 3
channels = [ChannelDef("DAPI", 0x6666FF), ChannelDef("Cy5", 0xFF0000)]
num_slices = 4
num_frames = 5
img_width = 256
img_height = 200
pixel_type = Values.PIX_TYPE_GRAY_16
bit_depth = 14
pixel_size = 0.5

# annotate channel names and colors

# create data set writer
ds_writer = DatasetWriter()
additional_info = {"Description": "Test data set"}
# first we define data set location and name, as well as the range of coordinates (mandatory)
print("Creating new data set %s in %s, existing one (if any) will be deleted." % (ds_name, args.path))
ds_writer.open(args.path, ds_name, positions=num_positions, channels=len(channels), z_slices=4, frames=num_frames,
               overwrite=True, additional_meta=additional_info)

# next we define image dimensions and pixel characteristics (mandatory)
ds_writer.initialize(img_width, img_height, pixel_type, bit_depth)

# finally we set important data set properties (optional)
ds_writer.set_pixel_size(pixel_size)
ds_writer.set_channel_data(channels)  # channel names and colors

time_ms = 0.0
interval_ms = 500
start_z_um = 0.0
z_step_um = 1.5
print("Adding images to dataset...")
for p in range(num_positions):
    ds_writer.set_position_name(p, "POS-%02d" % p)
    for f in range(num_frames):
        z_um = start_z_um
        for z in range(num_slices):
            for c in range(len(channels)):
                img_meta = {}
                img_meta[ImageMeta.ELAPSED_TIME_MS] = time_ms
                img_meta[ImageMeta.ZUM] = z_um
                img_meta[ImageMeta.XUM] = p * 13.0
                img_meta[ImageMeta.YUM] = p + 12.0
                img_meta[ImageMeta.CHANNEL_NAME] = channels[c]
                img = np.random.randint(2 ** bit_depth - 1, size=(img_height, img_width)).astype('uint16')
                ds_writer.add_image(img, position=p, channel=c, z_slice=z, frame=f, additional_meta=img_meta)
            z_um += z_step_um
        time_ms += interval_ms
# close and save
ds_writer.close()
print("Dataset completed and closed.")

# now we attempt to read the new dataset
ds_path = os.path.join(args.path, ds_name)
ds_reader = DatasetReader(os.path.join(args.path, ds_name))
print("Loading dataset from : " + ds_path)
print(
    "Positions: %d, Channels: %d, Slices: %d, Frames: %d, Image: %d X %d X %s" % (
    ds_reader.num_positions(), ds_reader.num_channels(),
    ds_reader.num_z_slices(), ds_reader.num_frames(),
    ds_reader.width(), ds_reader.height(),
    ds_reader.pixel_type()))
print("Channel names: " + str(ds_reader.channel_names()))
print("Position labels: " + str(ds_reader.position_labels()))

print("Summary metadata:")
print(json.dumps(ds_reader.summary_metadata(), indent=4))

print("\nImage list:")
for p in range(ds_reader.num_positions()):
    print("\nPosition %s, index=%d: " % (ds_reader.position_labels()[p], p))
    for c in range(ds_reader.num_channels()):
        for s in range(ds_reader.num_z_slices()):
            for f in range(ds_reader.num_frames()):
                try:
                    # get pixels
                    img = ds_reader.image_pixels(position_index=p, channel_index=c, z_index=s, t_index=f)
                    # get meta
                    img_meta = ds_reader.image_metadata(position_index=p, channel_index=c, z_index=s, t_index=f)

                    print("Image(p=%d c=%d, s=%d, f=%d): %s, %s, %s, %d X %d" %
                          (p, c, s, f,
                           ds_reader.get_position_name(p),
                           img_meta[ImageMeta.FILE_NAME],
                           img.dtype.name, img.shape[1], img.shape[0]))
                except G2SDataError as err:
                    print("Image(p=%d, c=%d, s=%d, f=%d) is not available: %s" % (p, c, s, f, err.__str__()))
                except KeyError as err:
                    print(
                        'Image(p=%d c=%d, s=%d, f=%d) coordinates not available in metadata: %s. Dataset incomplete.' %
                        (p, c, s, f, err.__str__()))
