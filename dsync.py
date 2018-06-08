"""

"""
from dsync.arguments import Arguments
from dsync.logger import Logger
from dsync.timer import Timer
from dsync.uploader import Uploader
from dsync.auth import Auth


class Dsync:
    def __init__(self, args):
        self.timer = Timer().start()
        self.args = args
        self.logger = Logger.create(
            name=__name__,
            level=args.log_level)
        self.uploader = Uploader(
            target_dir=args.directory,
            chunk_size=args.chunk_size,
            custom_ignore=args.ignore,
            dryrun=args.dryrun)
        self.auth = Auth(access_token=args.access_token)

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
        self.logger.info('Exiting %s' % self.timer.stop())
        return self


if __name__ == '__main__':
    Dsync(args=Arguments.create().parse()).execute().exit()
