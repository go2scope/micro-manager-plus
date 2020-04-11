import argparse
# parse command line arguments
from dataio.g2sdataset.g2sdataset import G2SDatasetWriter

parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path for the generated dataset')
args = parser.parse_args()

ds_writer = G2SDatasetWriter()
ds_name = "WriteTest"
ds_writer.create(args.path, ds_name, overwrite=True)
