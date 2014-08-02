#!/usr/bin/python

# This file is part of Snotra-backup.
#
# Snotra-backup is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# Snotra-backup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Snotra-backup; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Author: Thomas Jensen
#
# $Revision$

__author__ = "Thomas Jensen"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2014 Thomas Jensen"
__license__ = "GPL"

version = "0.1.0"

import ConfigParser, subprocess, logging, shlex, os, re, sys

Config = ConfigParser.ConfigParser()
Config.read("/etc/snotra/snotra.conf")

log_file = Config.get('DEFAULT', 'log_file')
logging.basicConfig(filename=log_file,format='%(asctime)s %(levelname)s\t%(message)s',level=logging.DEBUG)

gpg_passphrase = Config.get('DEFAULT', 'gpg_passphrase')
target_folder = Config.get('DEFAULT', 'target_folder')

full_if_older   = Config.get('DEFAULT', 'full-if-older-than')
remove_if_older = Config.get('DEFAULT', 'remove-older-than')

db_user = Config.get('DEFAULT', 'db_user')
db_pass = Config.get('DEFAULT', 'db_pass')

gsutil_enable = Config.getboolean('DEFAULT', 'gsutil_enable')
gsutil_folder = Config.get('DEFAULT', 'gsutil_folder')
gs_bucket     = Config.get('DEFAULT', 'gs_bucket')

logging.info('Running Snotra-backup')

duplicity_log = '/tmp/duplicity.log'

if len(sys.argv) > 1:
  args = sys.argv
  del args[0]
  logging.debug('Argument List: %s', str(args))

def RunCommand(command, duplicity = False):
  FNULL = open(os.devnull, 'w') 
  logging.debug('CMD: %s' % command)

  if not '--dry' in sys.argv:
    subprocess.call(shlex.split(command), stdout=FNULL, stderr=subprocess.STDOUT)
  else:
    print shlex.split(command)

  if duplicity:
    try:
      with open (duplicity_log, "r") as myfile:
        data=myfile.read().split('\n\n')
        for logline in data:
          if not re.match('^(WARNING) 1', logline) and not logline == '':
            logging.info(logline.replace('\n.',''))
      os.remove(duplicity_log)
    except IOError:
      logging.error('Error processing log file: %s', duplicity_log)

os.environ["PASSPHRASE"] = gpg_passphrase

for (i, item) in enumerate(Config.sections()):

    # Is the definition enabled?
    enabled = Config.getboolean(item, 'enabled')

    # What files to back-up?
    source = Config.get(item, 'source')

    # Is a database defined? If not; set empty.
    try:
      database = Config.get(item, 'database')
    except ConfigParser.NoOptionError:
      database = None

    # Is a target defined? If not; use same as source.
    try:
      target = Config.get(item, 'target')
    except ConfigParser.NoOptionError:
      target = source

    # Is a pre action defined? If not; set empty.
    try:
      pre_action = Config.get(item, 'pre_action')
    except ConfigParser.NoOptionError:
      pre_action = None

    # Is a post action defined? If not; set empty.
    try:
      post_action = Config.get(item, 'post_action')
    except ConfigParser.NoOptionError:
      post_action = None

    # Check if full_if_older and complete the option.
    if not full_if_older == '':
      full_if_older_str = '--full-if-older-than %s' % full_if_older

    
    if enabled:

      logging.info('Start: %s', item)

      if not pre_action == None:
        pre_command = (pre_action % {'source': source, 'target': target})
        RunCommand(pre_command)

      if not database == None:
        for (y, db_item) in enumerate(database.split(',')):
          db_command = ('mysqldump -u%(db_user)s -p%(db_pass)s %(db)s --result-file=%(source)s/%(db)s.sql' %
                       {'db_user': db_user, 'db_pass':db_pass, 'db':db_item.strip(), 'source': source})
          RunCommand(db_command)
          
      cp_command = ('duplicity %(full_if_older)s %(source)s file://%(folder)s%(target)s --log-file %(log)s' %
                   {'full_if_older': full_if_older_str, 'source': source, 'folder': target_folder, 'target': target, 'log': duplicity_log})
      RunCommand(cp_command, True)

      if not remove_if_older == '':
        rm_command = ('duplicity remove-older-than %(remove_if_older)s --force file://%(folder)s%(target)s --log-file %(log)s' %
                     {'remove_if_older': remove_if_older, 'folder': target_folder, 'target': target, 'log': duplicity_log})
        RunCommand(rm_command, True)

      if not post_action == None:
        post_command = (post_action % {'source': source, 'target': target})
        RunCommand(post_command)

      logging.info('Finished: %s', item)

if gsutil_enable:
  logging.info('Synchronizing to: %s', 'Google Cloud Storage')
  gsutil_cmd = ('%(folder)s/gsutil -m -q rsync -d -r %(target)s gs://%(bucket)s' %
               {'folder': gsutil_folder, 'target': target_folder, 'bucket': gs_bucket})
  RunCommand(gsutil_cmd)

logging.info('All done, exiting...\n')
