import argparse

from dataio import g2sdataset
from dataio.g2sdataset import G2SDatasetReader, G2SDataError
import json

# parse command line arguments


parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path of the data set')
args = parser.parse_args()

# load data set and print basic info
ds = G2SDatasetReader(args.path)

print("Loaded dataio: " + args.path)
print(
    "Positions: %d, Channels: %d, Slices: %d, Frames: %d, Image: %d X %d X %s" % (ds.num_positions(), ds.num_channels(),
                                                                                  ds.num_z_slices(), ds.num_frames(),
                                                                                  ds.width(), ds.height(),
                                                                                  ds.pixel_type()))
print("Channel names: " + str(ds.channel_names()))
print("Position labels: " + str(ds.position_labels()))

print("Summary metadata:")
print(json.dumps(ds.summary_metadata(), indent=4))

print("\nImage list:")
for p in range(ds.num_positions()):
    print("\nPosition: " + ds.position_labels()[p])
    for c in range(ds.num_channels()):
        for s in range(ds.num_z_slices()):
            for f in range(ds.num_frames()):
                try:
                    # get pixels
                    img = ds.image_pixels(position_index=p, channel_index=c, z_index=s, t_index=f)
                    # get meta
                    img_meta = ds.image_metadata(position_index=p, channel_index=c, z_index=s, t_index=f)

                    print("Image(c=%d, s=%d, f=%d): %s, %s, %d X %d" % (c, s, f, img_meta[g2sdataset.ImageMeta.FILE_NAME],
                                                                        img.dtype.name, img.shape[0], img.shape[1]))
                except G2SDataError as err:
                    print("Image(c=%d, s=%d, f=%d) is not available")
