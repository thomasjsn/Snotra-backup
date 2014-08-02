#!/usr/bin/python

# This file is part of Snotra-backup.
#
# Author: Thomas Jensen
#
# $Revision$

__author__ = "Thomas Jensen"
__version__ = "$Revision$"
__date__ = "$Date$"
__copyright__ = "Copyright (c) 2014 Thomas Jensen"
__license__ = "MIT"

version = "0.2.0"

import ConfigParser, subprocess, logging, shlex, os, re, sys, getopt

sys.path.insert(1, "/usr/local/share/snotra")

dry_run = False
config_file = "/etc/snotra/snotra.conf"

try:                                
  opts, args = getopt.getopt(sys.argv[1:], "dc:v", ["dry-run", "config="])
except getopt.GetoptError:
  print "Error handling command-line arguments"
  exit(2)

for opt, arg in opts:
  if opt in ("-d", "--dry-run"):
    dry_run = True

  elif opt in ("-c", "--config"):
    if os.path.isfile(arg):
      config_file = arg

  elif opt == '-v':
    print ('%(app)s ver. %(ver)s' % {'app': sys.argv[0], 'ver': version})
    exit(0)

Config = ConfigParser.ConfigParser()
Config.read(config_file)

log_file = Config.get('DEFAULT', 'log_file')
logging.basicConfig(filename=log_file,format='%(asctime)s %(levelname)s\t%(message)s',level=logging.DEBUG)

logging.info('Running Snotra-backup')
logging.info('Using config: %s', config_file)

gpg_passphrase = Config.get('DEFAULT', 'gpg_passphrase')
target_folder = Config.get('DEFAULT', 'target_folder')

full_if_older   = Config.get('DEFAULT', 'full-if-older-than')
remove_if_older = Config.get('DEFAULT', 'remove-older-than')

db_user = Config.get('DEFAULT', 'db_user')
db_pass = Config.get('DEFAULT', 'db_pass')

gsutil_enabled = Config.getboolean('DEFAULT', 'gsutil_enabled')
gsutil_folder  = Config.get('DEFAULT', 'gsutil_folder')
gs_bucket      = Config.get('DEFAULT', 'gs_bucket')

s3cmd_enabled = Config.getboolean('DEFAULT', 's3cmd_enabled')
s3cmd_folder  = Config.get('DEFAULT', 's3cmd_folder')
s3_bucket      = Config.get('DEFAULT', 's3_bucket')

duplicity_log = '/tmp/duplicity.log'

if len(sys.argv) > 1:
  args = sys.argv
  del args[0]
  logging.debug('Argument List: %s', str(args))

def RunCommand(command, duplicity = False):
  FNULL = open(os.devnull, 'w') 
  logging.debug('CMD: %s' % command)

  if not dry_run:
    if not duplicity:
      subprocess.call(shlex.split(command))
    else:
      subprocess.call(shlex.split(command), stdout=FNULL, stderr=subprocess.STDOUT)
  else:
    print shlex.split(command)

  if duplicity and not dry_run:
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

if gsutil_enabled:
  logging.info('Synchronizing to: %s', 'Google Cloud Storage')
  gsutil_cmd = ('%(folder)s/gsutil -m -q rsync -d -r %(target)s gs://%(bucket)s' %
               {'folder': gsutil_folder, 'target': target_folder, 'bucket': gs_bucket})
  RunCommand(gsutil_cmd)

if s3cmd_enabled:
  logging.info('Synchronizing to: %s', 'Amazon AWS')
  s3cmd_cmd = ('%(folder)s/s3cmd -q sync --delete-removed -r %(target)s gs://%(bucket)s' %
               {'folder': s3cmd_folder, 'target': target_folder, 'bucket': s3_bucket})
  RunCommand(s3cmd_cmd)


logging.info('All done, exiting...\n')
