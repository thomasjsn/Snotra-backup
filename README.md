# Snotra-backup
In Norse mythology, Snotra (Old Norse "clever") is a goddess associated with wisdom.

Snotra-backup is a backup script that uses *duplicity* and *mysqldump* to back up and encrypt files, folders and databases. It supports multiple
backends, and it can synchronize the backups with Google Cloud Storage and/or Amazon AWS (untested). In addition you can write your own command that is
executed when all backup definitions are done, that way you can move, copy or upload the files wherever. It is up to you.

## Requirements
* [Python](https://www.python.org/)
* [duplicity](http://duplicity.nongnu.org/)
* [mysqldump](http://www.linuxcommand.org/man_pages/mysqldump1.html) (if backing up databases)
* [NcFTP](http://www.ncftp.com/) (if backend 'ftp')
* [gsutil](https://developers.google.com/storage/docs/gsutil) (if sync with Google Cloud Storage)
* [s3cmd](http://s3tools.org/s3cmd) (if sync with Amazon AWS)

## Supported backends
* file
* ftp
* ssh

## Installation
Create symbolic link for shared library files:
```bash
$ sudo ln -s /path/to/snotra/share/ /usr/local/share/snotra
```

Create symbolic link in `/usr/local/sbin` folder, this is not required but will make Snotra system-wide available for the root user:
```bash
$ sudo ln -s /path/to/snotra/snotra.py /usr/local/sbin/snotra.py
```

## Command-line arguments
Argument | Action
--- | ---
`-s, --show` | Show all commands, but do nothing.
`-n, --dry-run` | Show that would have been done, but do nothing.
`-c, --config <file>` | Run with the spesified config file.
`-v` | Print version.

## Config file
The config file is read from `/etc/snotra/snotra.conf`. A sample config is provided, make your changes and copy it to `/etc/snotra/snotra.conf`. See comments in [snotra.conf.sample](snotra.conf.sample) for parameters.

## Cron job
Create file `/etc/cron.d/snotra` with the content below, this make will make Snotra run every night at 3:30:

```cron
MAILTO=root

# Run daily backup
30 3 * * * root [ -x /usr/local/sbin/snotra.py ] && /usr/local/sbin/snotra.py
```

## Log file
Snotra-backup logs to `/var/log/snotra.log` by default, but this can be changed in the config file.

### Log rotate
Since the log file can get pretty big over time it's wise to rotate it every now and then. Create file `/etc/logrotate.d/snotra` with the content below, this will make logrotate pick up the logfile:

```logrotate
/var/log/snotra.log {
        weekly
        rotate 4
        missingok
        compress
        delaycompress
        notifempty
        create 640 root adm
}
```

## Issues
The application is still work in progress so there may be bugs. Please report all bugs to the issue tracker on this repository ([here](https://github.com/HebronNor/Snotra-backup/issues)).

## Author
Thomas Jensen

## Lisence
```
The MIT License (MIT)

Copyright (c) 2014 Thomas Jensen

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
