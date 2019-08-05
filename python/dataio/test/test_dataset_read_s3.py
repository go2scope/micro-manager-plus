from dataio.g2sdataset import G2SDatasetReaderS3

from awslp.awslp import Cognito
from dataio.test.aws_config import AWS_CONFIGURATION

cognito = Cognito(application_id=AWS_CONFIGURATION['application_id'],
                  user_pool_id=AWS_CONFIGURATION['user_pool_id'],
                  identity_pool_id=AWS_CONFIGURATION['identity_pool_id'],
                  region_name=AWS_CONFIGURATION['region_name'])

username = 'lazar'
password = '123qwe'
image_dir = 'images'
image_name = 'img_000000000_Violet_012.tif'
dataset_name = 'lazar/NIH3T3_1'

identity_id, access_key_id, secret_key, session_token = cognito.get_aws_credentials(username=username,
                                                                                    password=password)

dr_s3 = G2SDatasetReaderS3(dataset_name,
                           AWS_CONFIGURATION['s3_bucket_name'],
                           AWS_CONFIGURATION['region_name'],
                           access_key_id,
                           secret_key,
                           session_token)

print('Dataset name   : ', dr_s3.name())
print('Num of channels: ', dr_s3.num_channels())
print('Width          : ', dr_s3.width())
print('Height         : ', dr_s3.height())
print('Pixel type     : ', dr_s3.pixel_type())