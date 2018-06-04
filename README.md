# dsync
[![Build Status](https://travis-ci.org/announce/dsync.svg?branch=master)](https://travis-ci.org/announce/dsync)

Sync a given directory to Dropbox

## Usage

0. Access token is available at [App Console](https://www.dropbox.com/developers/apps/) in Dropbox Developer site
0. Upload your target directory

```bash
$ export DSYNC_ACCESS_TOKEN="..."
$ nohup python dsync.py /Volumes/sdcz43/ &
```

## Development

 ```bash
$ ./dsy init
$ pip install -r requirements.txt
```

```bash
$ ./dsy lint
```
