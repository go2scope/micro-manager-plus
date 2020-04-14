import argparse
# parse command line arguments
import numpy as np

from dataio.g2sdataset.dataset import Values, SummaryMeta, ImageMeta, ChannelDef
from dataio.g2sdataset.writer import DatasetWriter

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
ds_writer.open(args.path, ds_name, positions=num_positions, channels=len(channels), z_slices=4, frames=num_frames,
               overwrite=True, additional_meta=additional_info)

# next we define image dimensions and pixel characteristics (mandatory)
ds_writer.initialize(img_width, img_height, pixel_type, bit_depth)

# finally we set important data set properties (optional)
ds_writer.set_pixel_size(pixel_size)
ds_writer.set_channel_data(channels) # channel names and colors

time_ms = 0.0
interval_ms = 500
start_z_um = 0.0
z_step_um = 1.5
for p in range(num_positions):
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
                # img_meta[ImageMeta.POS_NAME] = "POS-%d" % p
                img = np.random.randint(2 ** bit_depth - 1, size=(img_height, img_width)).astype('uint16')
                ds_writer.add_image(img, position=p, position_name="POS-%d" % p, channel=c, z_slice=z, frame=f,
                                    additional_meta=img_meta)
            z_um += z_step_um
        time_ms += interval_ms

ds_writer.close()
