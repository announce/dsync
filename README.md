# dsync
[![Build Status](https://travis-ci.org/announce/dsync.svg?branch=master)](https://travis-ci.org/announce/dsync)

Sync a given directory to Dropbox

## Usage

1. Access token is available at [App Console](https://www.dropbox.com/developers/apps/) in Dropbox Developer site
1. Upload your target directory

```bash
$ export DSYNC_ACCESS_TOKEN="..."
$ nohup python dsync.py /Volumes/sdcz43/ &
```

## Motivation
* Why not use an official client?
  * Because there’s no official way to upload files stored in external device such as USB memory.

## Installation

 ```bash
$ ./dsy init
$ pip install -r requirements.txt
```

## Development

```bash
$ ./dsy lint
```
