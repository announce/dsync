from argparse import ArgumentParser
import humanfriendly
from dsync.logger import Logger
from dsync.uploader import Uploader


class Arguments:

    def __init__(self, parser):
        self.parser = parser

    @classmethod
    def create(cls):
        return cls(parser=cls.generate_parser())

    @classmethod
    def generate_parser(cls):
        parser = ArgumentParser(description=u'dsync -- Sync a given directory to Dropbox')
        parser.add_argument(
            'directory',
            help='Local directory to upload')
        # @TODO https://pypi.org/project/python-daemon/
        # parser.add_argument(
        #     '-d',
        #     '--daemon',
        #     action='store_true',
        #     help='Run as daemon to watch target directory')
        parser.add_argument(
            '-n',
            '--dryrun',
            action='store_true',
            help='List up target files as noop')
        parser.add_argument(
            '-l',
            '--log-level',
            choices=Logger.available_levels(),
            default=Logger.AVAILABLE_LEVEL.get('INFO'),
            help='Choose log level from %s. The default level is %s.' % (
                Logger.AVAILABLE_LEVEL,
                Logger.AVAILABLE_LEVEL.get('INFO')))
        parser.add_argument(
            '-i',
            '--ignore',
            help='Specify path to configuration file')
        parser.add_argument(
            '-s',
            '--chunk-size',
            default=Uploader.CHUNK_SIZE_BYTE,
            help=' '.join([
                'Chunk size',
                '(see https://www.dropbox.com/developers/documentation/http/documentation#files-upload_session-start).',
                'The default size is %s.' % humanfriendly.format_size(Uploader.CHUNK_SIZE_BYTE, binary=True)
            ]))
        parser.add_argument(
            '-t',
            '--access-token',
            type=str,
            help=' '.join([
                'Access token',
                '(see https://www.dropbox.com/developers/apps).',
                'You also can specify it by the environment valuable \'DSYNC_ACCESS_TOKEN\''])
        )
        return parser

    def parse(self):
        return self.parser.parse_args()
