#!/usr/bin/env python
#
# Copyright 2013 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import optparse
import os
import sys

from util import build_utils


_RESOURCE_CLASSES = [
    "R.class",
    "R##*.class",
    "Manifest.class",
    "Manifest##*.class",
]


def Jar(class_files, classes_dir, jar_path, manifest_file=None):
  jar_path = os.path.abspath(jar_path)

  # The paths of the files in the jar will be the same as they are passed in to
  # the command. Because of this, the command should be run in
  # options.classes_dir so the .class file paths in the jar are correct.
  jar_cwd = classes_dir
  class_files_rel = [os.path.relpath(f, jar_cwd) for f in class_files]
  jar_cmd = ['jar', 'cf0', jar_path]
  if manifest_file:
    jar_cmd[1] += 'm'
    jar_cmd.append(os.path.abspath(manifest_file))
  jar_cmd.extend(class_files_rel)

  if not class_files_rel:
    empty_file = os.path.join(classes_dir, '.empty')
    build_utils.Touch(empty_file)
    jar_cmd.append(os.path.relpath(empty_file, jar_cwd))
  build_utils.CheckOutput(jar_cmd, cwd=jar_cwd)
  build_utils.Touch(jar_path, fail_if_missing=True)


def JarDirectory(classes_dir, jar_path, manifest_file=None, predicate=None):
  class_files = build_utils.FindInDirectory(classes_dir, '*.class')
  if predicate:
    class_files = [f for f in class_files if predicate(f)]

  Jar(class_files, classes_dir, jar_path, manifest_file=manifest_file)


def main():
  parser = optparse.OptionParser()
  parser.add_option('--classes-dir', help='Directory containing .class files.')
  parser.add_option('--input-jar', help='Jar to include .class files from')
  parser.add_option('--jar-path', help='Jar output path.')
  parser.add_option('--excluded-classes',
      help='GYP list of .class file patterns to exclude from the jar.')
  parser.add_option('--strip-resource-classes-for',
      help='GYP list of java package names exclude R.class files in.')
  parser.add_option('--stamp', help='Path to touch on success.')

  args = build_utils.ExpandFileArgs(sys.argv[1:])
  options, _ = parser.parse_args(args)
  # Current implementation supports just one or the other of these:
  assert not options.classes_dir or not options.input_jar

  excluded_classes = []
  if options.excluded_classes:
    excluded_classes = build_utils.ParseGypList(options.excluded_classes)

  if options.strip_resource_classes_for:
    packages = build_utils.ParseGypList(options.strip_resource_classes_for)
    excluded_classes.extend(p.replace('.', '/') + '/' + f
                            for p in packages for f in _RESOURCE_CLASSES)

  predicate = None
  if excluded_classes:
    predicate = lambda f: not build_utils.MatchesGlob(f, excluded_classes)

  with build_utils.TempDir() as temp_dir:
    classes_dir = options.classes_dir
    if options.input_jar:
      build_utils.ExtractAll(options.input_jar, temp_dir)
      classes_dir = temp_dir
    JarDirectory(classes_dir, options.jar_path, predicate=predicate)

  if options.stamp:
    build_utils.Touch(options.stamp)


if __name__ == '__main__':
  sys.exit(main())

