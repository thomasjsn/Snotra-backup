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

version = "0.3.0"

import ConfigParser, subprocess, logging, shlex, os, re, sys, getopt

# Make our share library folder available.
sys.path.insert(1, "/usr/local/share/snotra")

# Set default application arguments.
show_only = False
config_file = "/etc/snotra/snotra.conf"

# Read all command-line arguments.
try:                                
  opts, args = getopt.getopt(sys.argv[1:], "snc:v", ["show", "dry-run", "config="])
except getopt.GetoptError:
  print "Error handling command-line arguments"
  exit(2)

# Run though all arguments and handle them.
for opt, arg in opts:

  # Only show commands.
  if opt in ("-s", "--show"):
    show_only = True

  # Show what would have been done.
  if opt in ("-n", "--dry-run"):
    raise NotImplementedError, 'Not implemented yet...'

  # Optional config file.
  elif opt in ("-c", "--config"):
    if os.path.isfile(arg):
      config_file = arg

  # Print version information.
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
target_backend = Config.get('DEFAULT', 'target_backend')
target_folder  = Config.get('DEFAULT', 'target_folder')
target_host    = Config.get('DEFAULT', 'target_host')

host_user = Config.get('DEFAULT', 'host_user')
host_pass = Config.get('DEFAULT', 'host_pass')

full_if_older   = Config.get('DEFAULT', 'full-if-older-than')
remove_if_older = Config.get('DEFAULT', 'remove-older-than')

db_user = Config.get('DEFAULT', 'db_user')
db_pass = Config.get('DEFAULT', 'db_pass')

gsutil_enabled = Config.getboolean('DEFAULT', 'gsutil_enabled')
gsutil_folder  = Config.get('DEFAULT', 'gsutil_folder')
gs_bucket      = Config.get('DEFAULT', 'gs_bucket')

s3cmd_enabled = Config.getboolean('DEFAULT', 's3cmd_enabled')
s3cmd_folder  = Config.get('DEFAULT', 's3cmd_folder')
s3_bucket     = Config.get('DEFAULT', 's3_bucket')

cc_enabled = Config.getboolean('DEFAULT', 'cc_enabled')
cc_action  = Config.get('DEFAULT', 'cc_action')

target_backends = ['file', 'ftp', 'ssh']
target_prefix = ''

if not target_backend in target_backends:
  print 'Target backend error, allowed: %s' % ', '.join(target_backends)
  exit(2)

if target_backend in ['ftp', 'ssh']:
  target_prefix = ('%(backend)s://%(uid)s@%(host)s' % { 'backend': target_backend, 'uid': host_user, 'host': target_host })
else:
  target_prefix = '%s://' % target_backend

# Temp log file for duplicity log parser.
duplicity_log = '/tmp/duplicity.log'

# Print list of arguments in log file.
if len(sys.argv) > 1:
  args = sys.argv
  del args[0]
  logging.debug('Argument List: %s', str(args))

def RunCommand(command, duplicity = False):
  FNULL = open(os.devnull, 'w') 
  logging.debug('CMD: %s' % command)

  # Run command if not dry-run.
  if not show_only:
    if not duplicity:
      subprocess.call(shlex.split(command))
    else:
      subprocess.call(shlex.split(command), stdout=FNULL, stderr=subprocess.STDOUT)
  else:
    print shlex.split(command)

  # Log file parser for duplicity, but only if not dry-run.
  if duplicity and not show_only:
    try:
      with open (duplicity_log, "r") as myfile:
        data=myfile.read().split('\n\n')
        for logline in data:
          if not re.match('^(WARNING) 1', logline) and not logline == '':
            logging.info(logline.replace('\n.',''))
      os.remove(duplicity_log)
    except IOError:
      logging.error('Error processing log file: %s', duplicity_log)

# Set duplicity gpg passphrase as environment variable.
os.environ["PASSPHRASE"] = gpg_passphrase

# If backend is ftp ot ssh; set password as environment variable.
if target_backend in ['ftp', 'ssh'] and not target_backend == '':
  os.environ["FTP_PASSWORD"] = host_pass

# Enumerate through all backup definitios.
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

    # Carry of backup definition if enabled.
    if enabled:

      # Backup definition starting.
      logging.info('Start: %s', item)

      # If pre-action(s) is defined, run all of them.
      if not pre_action == None:
        for (x, pre_item) in enumerate(pre_action.split(',')):
          pre_command = (pre_item.strip() % {'source': source, 'target': target})
          RunCommand(pre_command)

      # If database(s) is defined, dump all of them.
      if not database == None:
        for (y, db_item) in enumerate(database.split(',')):
          db_command = ('mysqldump -u%(db_user)s -p%(db_pass)s %(db)s --result-file=%(source)s/%(db)s.sql' %
                       {'db_user': db_user, 'db_pass':db_pass, 'db':db_item.strip(), 'source': source})
          RunCommand(db_command)

      # Cleanup the extraneous duplicity files on the given backend.
      cl_command = ('duplicity cleanup --force %(prefix)s%(folder)s%(target)s --log-file %(log)s' %
                   {'prefix': target_prefix, 'folder': target_folder, 'target': target, 'log': duplicity_log})
      RunCommand(cl_command, True)
          
      # Do duplicity backup.
      cp_command = ('duplicity %(full_if_older)s %(source)s %(prefix)s%(folder)s%(target)s --log-file %(log)s' %
                   {'full_if_older': full_if_older_str, 'source': source, 'prefix': target_prefix, 'folder': target_folder, 'target': target, 'log': duplicity_log})
      RunCommand(cp_command, True)

      # If remove-if-older enabled, run command.
      if not remove_if_older == '':
        rm_command = ('duplicity remove-older-than %(remove_if_older)s --force %(prefix)s%(folder)s%(target)s --log-file %(log)s' %
                     {'remove_if_older': remove_if_older, 'prefix': target_prefix, 'folder': target_folder, 'target': target, 'log': duplicity_log})
        RunCommand(rm_command, True)

      # If post-action(s) is defined, run all of them.
      if not post_action == None:
        for (x, post_item) in enumerate(post_action.split(',')):
          post_command = (post_item.strip() % {'source': source, 'target': target})
          RunCommand(post_command)

      # Backup definition finished.
      logging.info('Finished: %s', item)

# Only do this if target backend is file.
if target_backend == 'file':

  # If gsutil is enabled, run it.
  if gsutil_enabled:
    logging.info('Synchronizing to: %s', 'Google Cloud Storage')
    gsutil_cmd = ('%(folder)s/gsutil -m -q rsync -d -r %(target)s gs://%(bucket)s' %
                 {'folder': gsutil_folder, 'target': target_folder, 'bucket': gs_bucket})
    RunCommand(gsutil_cmd)

  # If s3cmd is enabled, run it.
  if s3cmd_enabled:
    logging.info('Synchronizing to: %s', 'Amazon AWS')
    s3cmd_cmd = ('%(folder)s/s3cmd -q sync --delete-removed -r %(target)s gs://%(bucket)s' %
                {'folder': s3cmd_folder, 'target': target_folder, 'bucket': s3_bucket})
    RunCommand(s3cmd_cmd)

  # If custom command is enabled, run all of them.
  if cc_enabled:
    logging.info('Running custom command')
    for (x, cc_item) in enumerate(cc_action.split(',')):
      cc_command = (cc_item.strip() % {'target_folder': target_folder, 'log_file': log_file})
      RunCommand(cc_command)

# Backup is done.
logging.info('All done, exiting...\n')
