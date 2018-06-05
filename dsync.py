"""

"""
from argparse import ArgumentParser
from dsync.logger import Logger
from dsync.timer import Timer
from dsync.uploader import Uploader
from dsync.auth import Auth


class Dsync:
    def __init__(self, args):
        self.timer = Timer().start()
        self.args = args
        self.logger = Logger.create(name=__name__)
        self.uploader = Uploader(
            target_dir=args.directory,
            dryrun=args.dryrun
        )
        self.auth = Auth(access_token=args.token)

    def execute(self):
        self.logger.info('Started with %s %s' % (
            self.args.directory,
            '[dryrun]' if self.args.dryrun else '',
        ))
        self.uploader.ensure_client(
            token=self.auth.ensure_token()
        ).walk()
        return self

    def exit(self):
        self.logger.info('Exiting at %s' % self.timer.stop())
        return self


if __name__ == '__main__':
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
        '-t',
        '--token',
        type=str,
        help=' '.join([
            'Access token',
            '(see https://www.dropbox.com/developers/apps).',
            'You also can specify by the environment valuable \'DSYNC_ACCESS_TOKEN\''])
    )
    Dsync(args=parser.parse_args()).execute().exit()
