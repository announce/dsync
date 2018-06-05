import os
import six
import datetime
import time
from pathlib import Path
import unicodedata
import concurrent.futures

import dropbox

from dsync.app_error import AppError
from dsync.logger import Logger
from dsync.content_hasher import ContentHasher


class Uploader:
    """
    http://dropbox-sdk-python.readthedocs.io/en/latest/moduledoc.html#module-dropbox.dropbox
    """
    CHUNK_SIZE_BYTE = 100 * 1024 * 1024
    CH_BLOCK_BYTE = 4 * 1024 * 1024

    def __init__(self, target_dir, dryrun=True):
        self.logger = Logger.create(__name__)
        td = self.validate(target_dir)
        self.target_dir = td
        self.destination = os.path.basename(td)
        self.is_dryrun = dryrun
        self.ignore_files = self.ignore_files()
        self.client = None
        self.queued_futures = []

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
        with concurrent.futures.ThreadPoolExecutor(thread_name_prefix=__name__) as executor:
            for root, dirs, files in os.walk(self.target_dir):
                subdir = root[len(self.target_dir):].strip(os.path.sep)
                if any([part in self.ignore_files for part in subdir.split(os.path.sep)]):
                    self.logger.debug('Ignoring: %s' % subdir)
                    continue
                listing = self.list_folder(subdir=subdir)
                self.logger.debug('Descending into %s ...' % subdir)
                for name in files:
                    local_path = os.path.join(root, name)
                    future = executor.submit(
                        fn=self.task,
                        local_path=local_path,
                        subdir=subdir,
                        name=name,
                        listing=listing,
                    )
                    self.queued_futures.append(future)

            self.logger.info('Submitted %d task(s)' % len(self.queued_futures))
            for future in concurrent.futures.as_completed(self.queued_futures):
                try:
                    future.result()
                except Exception as exc:
                    self.logger.error('An unhandled exception: %s' % exc)

    def task(self, local_path, subdir, name, listing):
        if any([part in self.ignore_files for part in local_path.split(os.path.sep)]):
            self.logger.debug('Ignoring: %s' % local_path)
            return None
        name = name if isinstance(name, six.text_type) else name.decode('utf-8')
        nname = unicodedata.normalize('NFC', name)
        if nname in listing:
            md = listing[nname]
            if not self.is_synced(local_path, md):
                self.logger.debug('Changed since last sync: %s' % local_path)
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
        stat_eq = isinstance(md, dropbox.files.FileMetadata) and mtime_dt == md.client_modified and size == md.size
        if stat_eq:
            self.logger.debug('Meta data are matched (mtime_dt: %s, size: %s, local_path: %s)' % (
                mtime_dt,
                size,
                local_path,
            ))
            return True
        else:
            ch = self.content_hash(local_path)
            self.logger.debug('[%s] content_hash: (%s, %s)' % (
                'matched' if ch == md.content_hash else 'not matched',
                local_path,
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
            self.logger.warn('HttpError: %s', err)
            return None
        data = res.content
        self.logger.debug('Downloaded %d bytes; md: %s', len(data), md)
        return data

    def upload(self, local_path, subdir, name, overwrite=False):
        """Upload a file.
        Return the request response, otherwise None.
        """
        remote_path = self.remove_redundant_separator(self.destination, subdir, name)
        mode = (dropbox.files.WriteMode.overwrite
                if overwrite
                else dropbox.files.WriteMode.add)
        if self.is_dryrun:
            self.logger.info('[dryrun] Skipping target file (mode: %s, dryrun: %s, local: %s, remote: %s)' % (
                mode,
                self.is_dryrun,
                local_path,
                remote_path))
            return None
        try:
            result = self.upload_file(local_path, remote_path, mode)
        except dropbox.exceptions.DropboxException as err:
            self.logger.error('%r' % err)
            return None
        self.logger.debug('Uploaded %r' % result)
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
        while (fd.tell() < stat.st_size) and (tried < ideal_iteration * 2):
            tried += 1
            if (stat.st_size - fd.tell()) > self.CHUNK_SIZE_BYTE:
                self.logger.info('[#%s/%d] Appending file: (cursor.offset=%d, fd=%d, remote_path=%s)' % (
                    tried,
                    ideal_iteration,
                    cursor.offset,
                    fd.tell(),
                    remote_path,
                ))
                self.client.files_upload_session_append_v2(fd.read(self.CHUNK_SIZE_BYTE), cursor)
                cursor.offset = fd.tell()
            else:
                self.logger.info('Finishing transfer and committing %s' % remote_path)
                self.client.files_upload_session_finish(fd.read(self.CHUNK_SIZE_BYTE), cursor, commit)
        return commit
