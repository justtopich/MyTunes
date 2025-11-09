# Changelog

## 2.2.0-beta

This update improves working with covers - now it is have a separate settings and saving. 



### Fixed

* remove track from tracks will delete all lower tracks
* fail to convert file when trying to create output folder if it exists
* crashed when remove root item if it is a folder with a few nested items
* tracks space not show info in columns: bitrate, samplerate
* fail to convert few files with a same names
* fail to convert file if his duration is unknown (ffmpeg not show) 

### Improvements

* add splitter between file chooser and tracks viewer
* show info about image when mouse hover the cover
* select folder will select all nested items
* add splitter between files, tracks and metadata spaces. Now can change size each of them.
* add new columns to the tracks space: codec and cover types

## Features
* cover saving options.
* show image info when hover a cover
* support webp format for cover

## 2.1.0-beta

### Fixed
* calling ffmpeg with external console

### Features
* building with poetry


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
