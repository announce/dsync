import os
import six
import datetime
import time
from pathlib import Path
import unicodedata

import dropbox

from dsync.app_error import AppError
from dsync.logger import Logger
from dsync.content_hasher import ContentHasher


class Uploader:
    """
    http://dropbox-sdk-python.readthedocs.io/en/latest/moduledoc.html#module-dropbox.dropbox
    """
    CHUNK_SIZE_BYTE = 150 * 1024 * 1024
    CH_BLOCK_BYTE = 4 * 1024 * 1024

    def __init__(self, target_dir, dryrun=True):
        self.logger = Logger.create(__name__)
        td = self.validate(target_dir)
        self.target_dir = td
        self.destination = os.path.basename(td)
        self.is_dryrun = dryrun
        self.ignore_files = self.ignore_files()
        self.client = None

    @classmethod
    def validate(cls, target_dir):
        target = os.path.expanduser(target_dir)
        if not os.path.exists(target):
            raise AppError('%s does not exist on your filesystem' % target)
        if not os.path.isdir(target):
            raise AppError('%s is not a folder on your filesystem' % target)
        return target

    def ensure_client(self, token):
        self.client = dropbox.Dropbox(token)
        return self

    def walk(self):
        for root, dirs, files in os.walk(self.target_dir):
            subdir = root[len(self.target_dir):].strip(os.path.sep)
            listing = self.list_folder(subdir=subdir)
            self.logger.info('Descending into %s...' % subdir)

            for name in files:
                local_path = os.path.join(root, name)
                if any([part in self.ignore_files for part in local_path.split(os.path.sep)]):
                    self.logger.info('Ignoring: %s' % local_path)
                    break
                name = name if isinstance(name, six.text_type) else name.decode('utf-8')
                nname = unicodedata.normalize('NFC', name)
                if nname in listing:
                    md = listing[nname]
                    if not self.is_synced(local_path, md):
                        self.logger.info('%s has changed since last sync' % name)
                        self.upload(local_path, subdir, name, overwrite=True)
                else:
                    self.upload(local_path, subdir, name)

    @classmethod
    def normalized_mtime(cls, local_path):
        mtime = os.path.getmtime(local_path)
        return datetime.datetime(*time.gmtime(mtime)[:6])

    @classmethod
    def ignore_files(cls):
        with Path(Path(__file__).parent, 'ignore.csv').open() as fd:
            return [line.strip() for line in fd.readlines()]

    def is_synced(self, local_path, md):
        mtime_dt = self.normalized_mtime(local_path)
        size = os.path.getsize(local_path)
        self.logger.info('%r' % md)
        stat_eq = isinstance(md, dropbox.files.FileMetadata) and mtime_dt == md.client_modified and size == md.size
        if stat_eq:
            self.logger.info('Statically same (mtime_dt: %s, size: %s)' % (mtime_dt, size))
            return True
        else:
            ch = self.content_hash(local_path)
            self.logger.info('[%s] content_hash: %s' % (
                'matched' if ch == md.content_hash else 'not matched',
                ch,
            ))
            return ch == md.content_hash

    def content_hash(self, local_path):
        """
        https://www.dropbox.com/developers/reference/content-hash
        """
        hasher = ContentHasher()
        with open(local_path, 'rb') as fd:
            while True:
                chunk = fd.read(self.CH_BLOCK_BYTE)
                if len(chunk) == 0:
                    break
                hasher.update(chunk)
        return hasher.hexdigest()

    @classmethod
    def remove_redundant_separator(cls, destination, subdir, name=''):
        s = '%s/%s/%s' % (destination, subdir.replace(os.path.sep, '/'), name)
        return '/%s' % '/'.join(filter(None, s.split('/')))

    def list_folder(self, subdir):
        """List a folder.
        Return a dict mapping unicode filenames to
        FileMetadata|FolderMetadata entries.
        """
        remote_path = self.remove_redundant_separator(self.destination, subdir).rstrip('/')
        try:
            res = self.client.files_list_folder(remote_path)
        except dropbox.exceptions.ApiError as err:
            self.logger.warn('Folder listing failed for %s -- assumed empty: %s' % (remote_path, err))
            return {}
        else:
            rv = {}
            for entry in res.entries:
                rv[entry.name] = entry
            return rv

    def download(self, subdir, name):
        """Download a file.
        Return the bytes of the file, or None if it doesn't exist.
        """
        remote_path = self.remove_redundant_separator(self.destination, subdir, name)
        try:
            md, res = self.client.files_download(remote_path)
        except dropbox.exceptions.HttpError as err:
            self.logger.info('HttpError: %s', err)
            return None
        data = res.content
        self.logger.info('Downloaded %d bytes; md: %s', len(data), md)
        return data

    def upload(self, local_path, subdir, name, overwrite=False):
        """Upload a file.
        Return the request response, otherwise None.
        """
        remote_path = self.remove_redundant_separator(self.destination, subdir, name)
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        self.logger.info('mode: %s, dryrun: %s, local: %s, remote: %s' % (
            mode,
            self.is_dryrun,
            local_path,
            remote_path))
        if self.is_dryrun:
            return None
        try:
            result = self.upload_file(local_path, remote_path, mode)
        except dropbox.exceptions.ApiError as err:
            self.logger.warn('%s' % err)
            return None
        self.logger.info('Uploaded as %s' % result.name.encode('utf8'))
        self.logger.info('%r', result)
        return result

    def upload_file(self, local_path, remote_path, mode):
        with open(local_path, 'rb') as fd:
            stat = os.stat(local_path)
            if stat.st_size < self.CHUNK_SIZE_BYTE:
                return self.client.files_upload(
                    fd.read(), remote_path, mode,
                    client_modified=self.normalized_mtime(local_path),
                    autorename=True,
                    mute=True)
            else:
                return self.upload_large_file(fd=fd, remote_path=remote_path, stat=stat)

    def upload_large_file(self, fd, remote_path, stat):
        tried = 0
        session = self.client.files_upload_session_start(fd.read(self.CHUNK_SIZE_BYTE))
        cursor = dropbox.files.UploadSessionCursor(session.session_id, offset=fd.tell())
        commit = dropbox.files.CommitInfo(path=remote_path, autorename=True)
        ideal_iteration = stat.st_size // self.CHUNK_SIZE_BYTE
        while (fd.tell() < stat.st_size) or tried < ideal_iteration * 2:
            tried += 1
            self.logger.info('[#%s/%d] Sending chunk to %s' % (tried, ideal_iteration, remote_path))
            if (stat.st_size - fd.tell()) > self.CHUNK_SIZE_BYTE:
                self.logger.info('Appending file: cusor.offset=%d, fd is at %d' % (cursor.offset, fd.tell()))
                self.client.files_upload_session_append_v2(fd.read(self.CHUNK_SIZE_BYTE), cursor)
                cursor.offset = fd.tell()
            else:
                self.logger.info('Finishing transfer and committing')
                self.client.files_upload_session_finish(fd.read(self.CHUNK_SIZE_BYTE), cursor, commit)
        return commit
