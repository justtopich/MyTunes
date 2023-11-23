# MyTunes

Copy and convert audio files from music library to diferent place (such as microsd for music player) with saving metadata.

Can use Apple AAC encoder instead of FDK AAC for the better quality



## Installation

### QuickTime AAC encoder

Instead of ffmpeg AAC encoder (FDK) you can use Apple encoder without QuickTime installation.

1. Download **qaac (CLI QuickTime AAC/ALAC encoder)**
2. Place dll and exe files in **qaac** folder
3. Download the latest QTfiles.7z (if you are using qaac.exe) or QTfiles64.7z (if you are using qaac64.exe).
4. You nedd the **QTfiles** folder if you are using qaac.exe or **QTfiles64** folder if you are using qaac64.exe besides 
the qaac executable file.

Files tree
```
my_tunes
├─── qaac
│   ├─── qaac files
│   └─── lQTfiles64
│        └─ dll files
```

## Configuration
Settings are stored in **settings.ini**

### logging
- level - see python logging level
- max_mb - max size for log file before he will be zipped

### library
- root_path - source directory
- sync_path - destination directory wich files will ve copied/converted


### converter
- temp_path - temp directory
- ffmpeg - destination to executable ffmpeg
- qaac - destination to executable qaac
