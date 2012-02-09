#!/usr/bin/python
# Written by Gerhardus Geldenhuis <gerhardus.geldenhuis@gmail.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#

import yaml
import pprint
import sys
import argparse
import xmlrpclib

def process_input_file(filename):
  try:
    filehandle = open(filename, 'rU')
    dataMap = yaml.load(filehandle)
    filehandle.close
    pp = pprint.PrettyPrinter(indent=2)
    for server_def in dataMap:
      if not server_def['name'].startswith('reference'): # Ignore any templated data
        print server_def['name']
  except yaml.scanner.ScannerError as detail:
    print 'Your yaml is not up to scratch'
    print detail

def check_validity_against_cobbler():
  print 'looks valid'

def schema_validate(filename):
# function to be written in the future to validate the input file
# against a data template
  return True

def ltr(filename): #load test return 
  try:
    if schema_validate(filename):
      filehandle = open(filename, 'rU')
      dataMap = yaml.load(filehandle)
      filehandle.close
      return dataMap
  except yaml.scanner.ScannerError:
    print 'The yaml file parsed incorrectly, and needs fixing.'

# consider not handling this exception or adding the error message.
# Possibly this exception would be raised earlier if we were to do
# schema validation

def convert_eth(ifname,eth_settings):
# Cobbler wants interface names as part of the variable name when you set it.
# The function does the dictionary key convertion.
  new_eth = {}
  for value in eth_settings:
    new_eth[value+'-'+ifname] = eth_settings[value]    
  return new_eth

def add_servers_to_cobbler(server_data,server,username,password):
  try:
# I am currently using port forwarding when ssh'ing to a server. 
# Sometime in the future we might do this directly from a centralized
# place or just locally on the cobbler server when it first gets 
# commisioned by the puppet run.
# Until such time brush up on your -L flag skills in ssh.
    server = xmlrpclib.Server(server)
    token = server.login(username,password)
    for server_def in server_data:
      if not server_def['name'].startswith('reference'): # Ignore any templated server definitions
        system_id = server.new_system(token)
        for server_atrib in server_def:
          if server_atrib == 'interfaces': # Interfaces is dictionary on its own
            for interface in server_def['interfaces']:
              server.modify_system(system_id,'modify_interface',convert_eth(interface,server_def['interfaces'][interface]),token)
          else: # Add any attribute that is not an interface
            server.modify_system(system_id,server_atrib,server_def[server_atrib],token)
        server.save_system(system_id, token)
        print server_def['name'] + ' successfully added or modified'

  except xmlrpclib.Fault as detail:
    print detail

def main():
  parser = argparse.ArgumentParser(description='Converts yaml host templates into cobbler config and add it via XMLRPC')
  parser.add_argument('yaml_files', nargs='*')
  parser.add_argument('--action', choices=['add', 'test'],default='test', nargs=1, help='Add hosts to a cobbler server or test the config for validity')

  # The default value for server is for my own lazyness when I am port forwarding a cobbler server to my desktop
  parser.add_argument('--server', nargs=1, default='http://127.0.0.1:8080/cobbler_api', help='Server URL')
  parser.add_argument('-u','--username', nargs=1, default='cobbler')
  parser.add_argument('-p','--password', nargs=1, default='cobbler')
  args = parser.parse_args()

  if args.action[0] == 'add':
    for inputfile in args.yaml_files:
      add_servers_to_cobbler(ltr(inputfile),args.server,args.username,args.password) # use to add servers
      
  else:
    for inputfile in args.yaml_files:
      print 'Testing %s' % (inputfile)
      process_input_file(inputfile)  # use to test yaml
      print ''

if __name__ == '__main__':
  main()


# TODO

# flag to test file for accuracies against the cobbler instance

# Install/use rx library to do validation of yaml file
# http://stackoverflow.com/questions/6311738/create-a-model-from-yaml-json-on-the-fly
# http://stackoverflow.com/questions/1061482/why-isnt-this-a-valid-schema-for-rx
# http://www.kuwata-lab.com/kwalify/ruby/users-guide.01.html for ruby. Similar to Rx
# Add a test to not "enable" server when adding via XMLRPC, if the server already exists then don't add
#  maybe update instead...
