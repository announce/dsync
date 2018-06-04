import os
from dsync.app_error import AppError


class Auth:
    def __init__(self, access_token):
        self.access_token = access_token

    def ensure_token(self):
        if self.access_token is not None:
            return self.access_token
        if os.environ.get('DSYNC_ACCESS_TOKEN') is not None:
            return os.environ.get('DSYNC_ACCESS_TOKEN')
        raise AppError('Access token must be specified.')
