import argparse
# parse command line arguments
from dataio.g2sdataset.writer import DatasetWriter

parser = argparse.ArgumentParser()
parser.add_argument('path', help='directory path for the generated dataset')
args = parser.parse_args()

ds_writer = DatasetWriter()
ds_name = "WriteTest"
ds_writer.open(args.path, ds_name, overwrite=True)
