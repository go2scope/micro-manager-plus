"""
Test for ScopeSim class

Simulates a microscope equipped with a camera, focus stage and filter changer

"""
import scopesim
import argparse
import cv2

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path of the data set')
parser.add_argument('-scale', help='scaling factor for images', type=float, default=1.0)
args = parser.parse_args()

print('Initializing microscope with datasetOpenCV: ' + args.path)
scope = scopesim.ScopeSim()
scope.init(args.path, scale=args.scale)
print('Microscope ready.')

img = scope.get_image()
print("Current z=" + str(img.z))
print("Current channel=" + scope.get_channel_name())
zrange = scope.z_range()

center_z = zrange[0] + (zrange[1] - zrange[0])/2
print("Maximum stage range=" + str(zrange) + ", center=" + str(center_z))

# display image at specific offset from default
z = center_z - 9.8
print("Fetching image at z=" + str(z))
scope.set_z(z)
img = scope.get_image()

print('Image dimensions: ' + str(img.pixels.shape) + ', z=' + str(img.z))

# scale image for display to fit 800 X 800 box
imsize = max(img.pixels.shape)
display_size = min(800, imsize)
yscale = display_size / imsize
xscale = yscale

cv2.imshow('slice at z=' + str(img.z) + ' um',
           cv2.resize(img.pixels, None, fx=xscale, fy=yscale, interpolation=cv2.INTER_CUBIC))
cv2.waitKey(0)
cv2.destroyAllWindows()


