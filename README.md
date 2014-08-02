# Snotra-backup
In Norse mythology, Snotra (Old Norse "clever") is a goddess associated with wisdom.

Snotra-backup is a backup script that uses duplicity and mysqldump to backup up files, folders and databases.
It can also sync the backup folder with wither Google Cloud Storage or Amazon AWS, or both.

## Requirements
* [Python](https://www.python.org/)
* [duplicity](http://duplicity.nongnu.org/)
* [mysqldump](http://www.linuxcommand.org/man_pages/mysqldump1.html) (if backing up databases)
* [gsutil](https://developers.google.com/storage/docs/gsutil) (if sync with Google Cloud Storage)
* [s3cmd](http://s3tools.org/s3cmd) (if sync with Amazon AWS)

## Installation
Create symbolic link for shared library files:
```bash
$ ln -s /path/to/snotra/share/ /usr/local/share/snotra
```

Create symbolic link in `sbin` folder, this is not required but will make Snotra system-wide available for the root user:
```bash
$ ln -s /path/to/snotra/snotra.py /usr/local/sbin/snotra.py
```

## Command-line arguments
Argument | Action
--- | ---
`--dry` | Show all commands, but do nothing.

## Config file
The config file is normally placed in `/etc/snotra/snotra.conf`. See comments in [snotra.conf.sample] for parameters.

## Cron job
Create file `/etc/cron.d/snotra` with the content below, this make will make Snotra/etc/cron.d/snotra run every night at 3:30:

```cron
MAILTO=root

# Run daily backup
30 3 * * * root [ -x /usr/local/sbin/snotra.py ] && /usr/local/sbin/snotra.py
```

## Log rotate
TBD

## Lisence
GNU General Public License v.3

## Issues
The application is still work in progress so there may be bugs. Please report all bugs to the issue tracker on this repository ([here](https://github.com/HebronNor/Snotra-backup/issues)).
