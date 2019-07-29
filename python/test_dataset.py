import argparse
from dataset import g2sdataset
import cv2

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path of the data set')
args = parser.parse_args()

# load data set and print basic info
ds = g2sdataset.G2SPosDataset()
ds.load_meta(args.path)

print(f'Channels: {str(ds.num_channels())}, Slices: {str(ds.num_z_slices())}, Timepoints: {str(ds.num_frames())}')
channel = 0

if ds.num_channels() > 0 and ds.num_z_slices() > 0 and ds.num_frames() > 0:

    img = ds.image_pixels(channel_index=0, z_index=0, t_index=0)
    print('Image dimensions: ' + str(img.shape))

    # scale image for display to not exceed 800 X 800 box
    imsize = max(img.shape)
    display_size = min(800, imsize)
    yscale = display_size / imsize
    xscale = yscale

    cv2.imshow('image',
               cv2.resize(img, None, fx=xscale, fy=yscale, interpolation=cv2.INTER_CUBIC))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print('Data set is empty or invalid.')
