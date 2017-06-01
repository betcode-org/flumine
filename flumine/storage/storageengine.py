import os
import shutil
import zipfile
import logging


class BaseEngine:

    NAME = None

    def __init__(self):
        self.markets_loaded = []

    def __call__(self, market_id):
        file_dir = os.path.join('/tmp', '%s' % market_id)

        # check that file actually exists
        if not os.path.isfile(file_dir):
            logging.error('File: %s does not exist in /tmp' % market_id)
            return

        # zip file
        zip_file_dir = self.zip_file(file_dir, market_id)
        # core load code
        self.load(zip_file_dir)
        # clean up
        self.clean_up(file_dir, zip_file_dir)

        self.markets_loaded.append(market_id)

    def load(self, zip_file_dir):
        """Loads zip_file_dir to expected dir
        """
        raise NotImplementedError

    def validate_settings(self):
        """Validates settings e.g. directory
        provided, raises OSError
        """
        raise NotImplementedError

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
        }


class Local(BaseEngine):

    NAME = 'LOCAL'

    def __init__(self, directory):
        super(Local, self).__init__()
        self.directory = directory
        self.validate_settings()

    def validate_settings(self):
        if not os.path.isdir(self.directory):
            raise OSError('File dir %s does not exist' % self.directory)

    def load(self, zip_file_dir):
        shutil.copy(zip_file_dir, self.directory)
