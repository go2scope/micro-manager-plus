""" Rescale dataset
"""
import g2sdataset
import argparse

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('source', help='directory path of the input data set')
parser.add_argument('scale', help='scale')
args = parser.parse_args()

destination = args.source + "-scaled" + "-" + args.scale

g2sdataset.G2SDataset.rescale(args.source, destination, args.scale)

