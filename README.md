# dsync
[![Build Status](https://travis-ci.org/announce/dsync.svg?branch=master)](https://travis-ci.org/announce/dsync)

A CLI tool for one-way sync of a given directory towards Dropbox

## Usage

1. Create an app at [App Console](https://www.dropbox.com/developers/apps/) and retrieve an access token
1. Execute the script like below to upload your target directory:

```bash
$ export DSYNC_ACCESS_TOKEN="__YOUR_ACCESS_TOKEN_HERE__"
$ python dsync.py ~/Desktop/example-directory
```

## Motivation
* Why not use an official client?
  * Because there’s no official way to upload files stored in external device such as USB memory (in my case it's `/Volumes/sdcz43`).

## Installation

 ```bash
$ ./dsy init
```

## Development

```bash
$ ./dsy lint
```
