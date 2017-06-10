import os
import json
import shutil
import zipfile
import logging
import boto3
from boto3.s3.transfer import (
    S3Transfer,
    TransferConfig,
)
from botocore.exceptions import BotoCoreError


class BaseEngine:

    NAME = None

    def __init__(self, directory):
        self.directory = directory
        self.markets_loaded = []
        self.validate_settings()

    def __call__(self, market_id, market_definition):
        logging.info('Loading %s to %s:%s' % (market_id, self.NAME, self.directory))
        file_dir = os.path.join('/tmp', '%s' % market_id)

        # check that market has not already been loaded
        if market_id in self.markets_loaded:
            logging.error('File: /tmp/%s has already been loaded' % market_id)
            return

        # check that file actually exists
        if not os.path.isfile(file_dir):
            logging.error('File: %s does not exist in /tmp' % market_id)
            return

        # zip file
        zip_file_dir = self.zip_file(file_dir, market_id)
        # core load code
        self.load(zip_file_dir, market_definition)
        # clean up
        self.clean_up(file_dir, zip_file_dir)

        self.markets_loaded.append(market_id)

    def load(self, zip_file_dir, market_definition):
        """Loads zip_file_dir to expected dir
        """
        raise NotImplementedError

    def validate_settings(self):
        """Validates settings e.g. directory
        provided, raises OSError
        """
        pass

    @staticmethod
    def create_metadata(market_definition):
        try:
            del market_definition['runners']
        except KeyError:
            pass
        return dict([a, str(x)] for a, x in market_definition.items())

    @staticmethod
    def clean_up(file_dir, zip_file_dir):
        """remove txt file and zip from /tmp
        """
        os.remove(file_dir)
        os.remove(zip_file_dir)

    @staticmethod
    def zip_file(file_dir, market_id):
        """zips txt file into filename.zip
        """
        zip_file_directory = os.path.join('/tmp', '%s.zip' % market_id)
        zf = zipfile.ZipFile(zip_file_directory, mode='w')
        zf.write(file_dir, os.path.basename(file_dir), compress_type=zipfile.ZIP_DEFLATED)
        zf.close()
        return zip_file_directory

    @property
    def markets_loaded_count(self):
        return len(self.markets_loaded)

    @property
    def extra(self):
        return {
            'name': self.NAME,
            'markets_loaded': self.markets_loaded,
            'markets_loaded_count': self.markets_loaded_count,
            'directory': self.directory,
        }


class Local(BaseEngine):

    NAME = 'LOCAL'

    def validate_settings(self):
        if not os.path.isdir(self.directory):
            raise OSError('File dir %s does not exist' % self.directory)

    def load(self, zip_file_dir, market_definition):
        shutil.copy(zip_file_dir, self.directory)


class S3(BaseEngine):

    NAME = 'S3'

    def __init__(self, directory, access_key=None, secret_key=None):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
        )
        transfer_config = TransferConfig(use_threads=False)
        self.transfer = S3Transfer(self.s3, config=transfer_config)
        super(S3, self).__init__(directory)

    def validate_settings(self):
        # error raised if bucket not present
        self.s3.head_bucket(Bucket=self.directory)

    def load(self, zip_file_dir, market_definition):
        try:
            self.transfer.upload_file(
                filename=zip_file_dir,
                bucket=self.directory,
                key=os.path.basename(zip_file_dir),
                extra_args={
                    'Metadata': self.create_metadata(market_definition)
                }
            )
        except (BotoCoreError, Exception) as e:
            print(e)
