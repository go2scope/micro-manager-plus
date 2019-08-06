from dataio.g2sdataset import G2SDatasetReaderS3

from awslp.awslp import Cognito
from dataio.test.aws_config import AWS_CONFIGURATION

cognito = Cognito(application_id=AWS_CONFIGURATION['application_id'],
                  user_pool_id=AWS_CONFIGURATION['user_pool_id'],
                  identity_pool_id=AWS_CONFIGURATION['identity_pool_id'],
                  region_name=AWS_CONFIGURATION['region_name'])

dataset_name = 'nenad/Run_1'
# dataset_name = 'lazar/NIH3T3_1'
identity_id, access_key_id, secret_key, session_token = cognito.get_aws_credentials(username=AWS_CONFIGURATION['username'],
                                                                                    password=AWS_CONFIGURATION['password'])

dr_s3 = G2SDatasetReaderS3(dataset_name,
                           AWS_CONFIGURATION['s3_bucket_name'],
                           AWS_CONFIGURATION['region_name'],
                           access_key_id,
                           secret_key,
                           session_token)

print('Dataset name   : ', dr_s3.name())
print('Num of channels: ', dr_s3.num_channels())
print('Channels       : ', dr_s3.channel_names())
print('Width          : ', dr_s3.width())
print('Height         : ', dr_s3.height())
print('Pixel type     : ', dr_s3.pixel_type())
print('Frames         : ', dr_s3.num_frames())
print('Slices         : ', dr_s3.num_z_slices())
print()
print(dr_s3.image_pixels(0, 0, 0, 0))
print()
print(dr_s3.image_pixels(position_index=0, channel_index=2, z_index=0, t_index=30))
