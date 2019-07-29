import argparse
from dataset import g2sdataset

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path of the data set')
args = parser.parse_args()

# load data set and print basic info
ds = g2sdataset.G2SDatasetReader(args.path)

print("Loaded dataset: " + args.path)
print(
    "Positions: %d, Channels: %d, Slices: %d, Frames: %d, Image: %d X %d X %s" % (ds.num_positions(), ds.num_channels(),
                                                                                  ds.num_z_slices(), ds.num_frames(),
                                                                                  ds.width(), ds.height(),
                                                                                  ds.pixel_type()))
print("Channel names: " + str(ds.channel_names()))
print("Position labels: " + str(ds.position_labels()))

for p in range(ds.num_positions()):
    print("\nPosition: " + ds.position_labels()[p])
    for c in range(ds.num_channels()):
        for s in range(ds.num_z_slices()):
            for f in range(ds.num_frames()):
                print("Image(c=%d, s=%d, f=%d): %s" % (c, s, f, ds.image_metadata(position_index=p, channel_index=c,
                                                                                  z_index=s, t_index=f)[
                    g2sdataset.ImageMeta.FILE_NAME]))
