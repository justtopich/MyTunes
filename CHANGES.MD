# Changelog

## 2.1.0-beta
### Features
* add menu bar and settings
* add cpu threads settings

### Improvements
* add drag'n'drop from folders chooser
* listing drives in folders chooser

### Fixed
* in dark mode in processing window light text appears on light background
* some jpeg pictures can't read in mp3 files
* files with characters `[]` in names not see and not adding to converter
* processing can freezing with small files. ffmpeg stdout put to stderr

### Deprecated
* remove all library settings


## 2.0.0-beta

### Features

* add gui

### Improvements

* converter processing method now is asynchronous function that return task progressing [0-100]

### Fixed

* Integer tags (year, track number, etc,) raise exception if they have not digest char. Now it trying to parse them.

## 0.1.0

release
