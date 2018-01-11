#!/usr/bin/python3
''' update rules in suricata deployment
    sudo python3 suricata_et_rule_update.py
    __author__ = logoyda@gmail.com
'''

import io
import sys
import time
import gzip
import tarfile
import hashlib
import shutil
import yaml
import urllib.request
from os import path, listdir


def main():
  ''' set suricata / et variables
      download, extract, and move rules
      update yaml
  '''
  path_suricata = '/etc/suricata/'
  base_url = 'https://rules.emergingthreats.net/open/suricata-4.0-enhanced/'
  filename_rule_tar = 'emerging.rules.tar.gz'
  filename_rule_desc = 'SID-Descriptions-ETOpen.json.gz'
  filename_yaml = 'suricata-1.3-open.yaml'

  suri_files = [{'url': base_url+filename, 'path': path_suricata+filename}
                for filename in [filename_rule_tar, filename_rule_desc, filename_yaml]]

  # download, extract, move
  hash_diff = hash_local_vs_site(path_suricata+filename_rule_tar, base_url+filename_rule_tar+'.md5')
  if hash_diff:
    updated_files = download_suri_files(suri_files)
    extract_files(suri_files)
    move_files(f"/etc/suricata/{filename_rule_tar.replace('.tar.gz','')}/rules/", path_suricata+'rules/')

    # modify yaml
    if path_suricata+filename_yaml in updated_files:
      modify_et_suri_yaml(path_suricata+filename_yaml)
#
def hash_local_vs_site(path_local_file, url_site_md5):
  ''' hash local file and compare to hash at url '''
  print(f'comparing hash {path_local_file} with {url_site_md5}')

  diff = False
  if not path.exists(path_local_file):
    print(' new file')
    return True

  hash_local = hashlib.md5(open(path_local_file,'rb').read()).hexdigest()

  with urllib.request.urlopen(url_site_md5) as response:
    html = response.read()
    hash_site = html.decode('utf-8').strip()

  if hash_local != hash_site:
    diff = True

  print('', hash_local)
  print('', hash_site)
  print(' diff:', diff)

  return diff
#
def download_suri_files(file_list):
  ''' given list of files, download from url and save to path '''
  print('downloading files in list')
  updated_files = []
  for f in file_list:
    if path.exists(f['path']):
      print(f" {f['url']} to {f['path']}")
      urllib.request.urlretrieve(f['url'], f['path'], reporthook)
      print()
      updated_files.append(f['path'])
    else:
      print(f" new {f['path']}")
      urllib.request.urlretrieve(f['url'], f['path'], reporthook)
      print()
      updated_files.append(f['path'])
  return updated_files
#
def reporthook(count, block_size, total_size):
  ''' show progress for urlretrieve '''
  global start_time
  if count == 0:
    start_time = time.time()
    return
  duration = time.time() - start_time
  progress_size = int(count * block_size)
  speed = int(progress_size / (1024 * duration))
  percent = int(count * block_size * 100 / total_size)
  sys.stdout.write("\r...%d%%, %d MB, %d KB/s, %d seconds passed" %
                   (percent, progress_size / (1024 * 1024), speed, duration))
  sys.stdout.flush()
#
def extract_files(files):
  ''' unzip and untar .tar.gz files '''
  print('extracting files in list')
  for packed_file in files:
    print(' ', packed_file['path'])
    if packed_file['path'].endswith('gz'):
      packed_file['name'] = packed_file['path'].replace('.gz','')
      text = ''
      if packed_file['path'].endswith('.tar.gz'):
        packed_file['name'] = packed_file['name'].replace('.tar','')
        tar = tarfile.open(packed_file['path'], 'r:gz')
        tar.extractall(packed_file['name'])
        tar.close()
      else:
        text = unzip(packed_file['path'])
        if text:
          with open(packed_file['name'], 'wb') as outfile:
            outfile.write(text)
#
def unzip(file_path):
  ''' read gzip file into a string '''
  with gzip.open(file_path, 'rb') as f:
    return f.read()
#
def move_files(src_dir, dst_dir):
  ''' move all files from src_dir to dst_dir '''
  print(f'moving from {src_dir} to {dst_dir}')
  for source_file in listdir(src_dir):
    shutil.move(path.join(src_dir, source_file), path.join(dst_dir, source_file))
#
def modify_et_suri_yaml(path_yaml):
  ''' enable file log and create new log per run '''
  print('modifying yaml')
  f = read_file(path_yaml)
  yaml_parsed = yaml.load(f)
  index_file_log = next(index for (index, d) in enumerate(yaml_parsed['outputs']) if 'file-log' in d)
  yaml_parsed['outputs'][index_file_log]['file-log']['enabled'] = True
  yaml_parsed['outputs'][index_file_log]['file-log']['append'] = False

  rule_files = yaml_parsed['rule-files']
  rule_files.append('emerging-info.rules')

  yaml_dumped = yaml.dump(yaml_parsed, explicit_start=True, version=(1,1))
  write_file(path_yaml.replace('.yaml', '.modified.yaml'), yaml_dumped)
#
def read_file(path):
  ''' read file '''
  with io.open(path, "r", encoding="utf-8") as f:
    return f.read()
#
def write_file(path, content):
  ''' write content to file '''
  with io.open(path, 'w') as f:
    f.write(content)
#
if __name__ == '__main__':
  main()
