import argparse
import json

# parse command line arguments
from dataio.g2sdataset.g2sdataset import G2SDatasetReader, ImageMeta, G2SDataError

parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path of the data set')
args = parser.parse_args()

# load data set and print basic info
ds_reader = G2SDatasetReader(args.path)

print("Loaded dataio: " + args.path)
print(
    "Positions: %d, Channels: %d, Slices: %d, Frames: %d, Image: %d X %d X %s" % (ds_reader.num_positions(), ds_reader.num_channels(),
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

                    print("Image(c=%d, s=%d, f=%d): %s, %s, %s, %d X %d" %
                                                                    (c, s, f,
                                                                     ds_reader.get_position_dataset(p).position_index(),
                                                                     img_meta[ImageMeta.FILE_NAME],
                                                                     img.dtype.name, img.shape[0], img.shape[1]))
                except G2SDataError as err:
                    print("Image(p=%d, c=%d, s=%d, f=%d) is not available: %s" % (p, c, s, f, err.__str__()))
                except KeyError as err:
                    print(
                        'Image(p=%d c=%d, s=%d, f=%d) coordinates not available in metadata: %s. Dataset incomplete.' %
                        (p, c, s, f, err.__str__()))
