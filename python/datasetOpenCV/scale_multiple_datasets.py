""" Rescale multiple datasets automatically
"""
import g2sdataset
import argparse
import os

# parse command line arguments
parser = argparse.ArgumentParser()
parser.add_argument('source', help='directory path of the parent folder')
parser.add_argument('scale', help='scale')
args = parser.parse_args()

dataset_names = os.listdir(args.source)
for dir_name in dataset_names:
    if os.isdir(args.source + "/" + dir_name):
        print('Scaling datasetOpenCV: ' + dir_name)
        destination = args.source + "/" + dir_name + "-scaled" + "-" + args.scale
        g2sdataset.G2SDataset.rescale(args.source, destination, args.scale)

