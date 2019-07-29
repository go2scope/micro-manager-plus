""" Test example for g2sdataset module
"""

import argparse
import cv2

# parse command line arguments
from datasetOpenCV import g2sdataset

parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path of the data set')
parser.add_argument('-scale', help='scaling factor for images', type=float, default=1.0)
args = parser.parse_args()

# load data set and print basic info
ds = g2sdataset.G2SDataset()
print('Loading data set: ' + args.path + ", scaled by " + str(args.scale) + "...")
ds.load(args.path, scale=args.scale)
print('Finished loading data set.')

print(f'Channels: {str(ds.num_channels())}, Slices: {str(ds.num_zslices())}, Timepoints: {str(ds.num_frames())}')
channel = 0

if ds.num_channels() > 0 and ds.num_zslices() > 0 and ds.num_frames() > 0:

    # load image from the middle of the z stack, using first channel
    zpos = ds.num_zslices() // 2
    img = ds.image(0, zpos, 0)  # this is go2scope image
    print('Image dimensions: ' + str(img.shape) + ', z=' + str(img.z))

    # scale image for display to not exceed 800 X 800 box
    imsize = max(img.pixels.shape)
    display_size = min(800, imsize)
    yscale = display_size / imsize
    xscale = yscale

    cv2.imshow('slice at z=' + str(img.z) + ' um',
               cv2.resize(img.pixels, None, fx=xscale, fy=yscale, interpolation=cv2.INTER_CUBIC))
    cv2.waitKey(0)
    cv2.destroyAllWindows()
else:
    print('Data set is empty or invalid.')
