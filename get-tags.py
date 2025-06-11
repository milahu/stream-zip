#!/usr/bin/env python3

# old tags from https://github.com/toslunar/stream-zip
# new commits from https://github.com/ikreymer/stream-zip

# last tagged version in https://github.com/toslunar/stream-zip
stop_at_version = "0.0.57"

import os
import sys
import requests
from distutils.version import LooseVersion
import tarfile
import io
import hashlib
import subprocess

def sha1(_bytes):
  h = hashlib.new('sha1')
  h.update(_bytes)
  return h.hexdigest()

version4hash = dict()

# https://stackoverflow.com/questions/4888027/how-to-list-all-available-package-versions-with-pip
package_name = "stream-zip"
url = f"https://pypi.org/pypi/{package_name}/json"
data = requests.get(url).json()
versions = list(data["releases"].keys())
versions.sort(key=LooseVersion, reverse=True)
for version in versions:
  #print("version", version)
  for release in data["releases"][version]:
    if release["packagetype"] != "sdist":
      continue
    #print("release", release)
    url = release["url"]
    tar_bytes = requests.get(url).content
    # https://stackoverflow.com/questions/15857792/how-to-construct-a-tarfile-object-in-memory-from-byte-buffer-in-python-3
    tar = tarfile.open(fileobj=io.BytesIO(tar_bytes))
    for member in tar.getmembers():
      # stream_zip-0.0.83/stream_zip/__init__.py
      #print("member", member.name)
      file_name = member.name.split("/", 1)[-1]
      if file_name in ("stream_zip/__init__.py", "stream_zip.py"):
        file_bytes = tar.extractfile(member).read()
        file_hash = sha1(file_bytes)
        print(file_hash, version, file_name)
        break
    version4hash[file_hash] = version
  if version == stop_at_version:
    break

def get_file_name():
  file_name = "stream_zip/__init__.py"
  if not os.path.exists(file_name):
    file_name = "stream_zip.py"
  assert os.path.exists(file_name), f"missing file: {file_name}"
  return file_name

def get_file_hash():
  file_name = get_file_name()
  with open(file_name, "rb") as f:
    file_bytes = f.read()
  file_hash = sha1(file_bytes)
  return file_hash

def get_commit():
  return subprocess.check_output("git rev-parse HEAD".split(), text=True).strip()

subprocess.check_call("git checkout --force main".split())
last_commit = get_commit()
last_file_hash = get_file_hash()
while True:
  subprocess.check_call("git checkout HEAD^".split(), stderr=subprocess.DEVNULL)
  commit = get_commit()
  file_hash = get_file_hash()
  if file_hash != last_file_hash:
    # file changed
    last_version = version4hash.get(last_file_hash)
    if last_version:
      if last_version == stop_at_version:
        break
      cmd = f"git tag --force v{last_version} {last_commit}"
      print(cmd)
      subprocess.check_call(cmd.split())
    else:
      print(f"error: not found version of last_file_hash {last_file_hash}")
  last_commit = commit
  last_file_hash = file_hash
