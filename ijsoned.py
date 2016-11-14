#!/usr/bin/env python

from __future__ import print_function

from copy import deepcopy
import cmd
import json
import os
import sys

from jsonpath_rw import jsonpath, parse

class IJsonEdException(Exception):
  pass


class IJsonEd(object, cmd.Cmd):
  intro = "IJsonEd. Type help or ? to list commands."

  def __init__(self, doc, path):
    cmd.Cmd.__init__(self)
    self.doc = doc
    self.path = path

  @property
  def prompt(self):
    return '{}> '.format(self.path)

  def do_pwd(self, arg):
    """Display the current path"""
    print(self.path)

  def do_show(self, arg):
    """Display json at the current path or specified path"""
    try:
      show(self.doc, self.path, arg)
    except Exception as error:
      self.dump_error(error)

  def complete_show(self, text, line, begidx, endidx):
    return self.handle_completion(text, line, begidx, endidx)

  def do_edit(self, arg):
    """Change path in the json structure"""
    try:
      self.path = change_current(self.doc, self.path, arg)
    except Exception as error:
      self.dump_error(error)

  def complete_edit(self, text, line, begidx, endidx):
    return self.handle_completion(text, line, begidx, endidx)

  def do_summary(self, arg):
    """Display summary of current path or specified path"""
    try:
      show(self.doc, self.path, arg, summary_only=True)
    except Exception as error:
      self.dump_error(error)

  def complete_summary(self, text, line, begidx, endidx):
    return self.handle_completion(text, line, begidx, endidx)

  def do_up(self, arg):
    """Change path to one or more levels up the json structure"""
    try:
      self.path = change_up(self.path, arg)
    except Exception as error:
      self.dump_error(error)

  def do_top(self, arg):
    """Change path to root level"""
    self.path = '$'

  def do_set(self, arg):
    """Change specified path (. for current) to new value"""
    try:
      expr, new_value = arg.split()
      self.doc = modify(self.doc, self.path, expr, new_value)
    except Exception as error:
      self.dump_error(error)

  def do_exit(self, arg):
    """Exit ijsoned"""
    return True

  def do_EOF(self, arg):
    """EOF (ctrl-D) hook for exit"""
    print('exit')
    return True

  def dump_error(self, error):
    print(error, file=sys.stderr)

  def handle_completion(self, text, line, begidx, endidx):
#    print('>"{}" "{}" "{}" "{}"<'.format(text, line, begidx, endidx))
    val = line.split(' ', 1)[1]

    if val.startswith('$'):
      paths = []
    else:
      paths = [self.path]

    spec_path = val.rsplit('.', 1)
    search_path = spec_path[:-1]
    search_term = spec_path[-1]

    paths.extend(search_path)

    full_path = '.'.join(paths) # [:-1]).rstrip('.')

    jsonpath_expr = parse(full_path)
    match = jsonpath_expr.find(self.doc)

    result = []
    for curr in match:
      if type(curr.value) == dict:
        result.extend(['.'.join(search_path + [key]) for key in curr.value.keys() if key.startswith(search_term)])

    return result


def main(argv=sys.argv):
  root = {}
  if argv[1]:
    with open(argv[1]) as f_in:
      root = json.load(f_in)

  IJsonEd(root, '$').cmdloop()


def change_current(root, current, expr):
  joined = '.'.join([current, expr])
  jsonpath_expr = parse(joined)
  match = jsonpath_expr.find(root)
  if not match:
    raise IJsonEdException('Jsonpath expression {} has no match'.format(joined))
  first = match[0]
  # if not type(first) in (list, dict):
  #   raise IJsonEdException('Jsonpath of {} is a leaf'.format(joined))
  return str(first.full_path)


def change_up(current, expr):
  if not current:
    return current

  if expr:
    levels = int(expr)
  else:
    levels = 1

  while levels > 0:
    levels -= 1
    if current[-1] == ']':
      current = current.rsplit('[', 1)[0]
    else:
      if '.' in current:
        current = current.rsplit('.', 1)[0]
      else:
        current = '$'

  return current.rstrip('.')


def show(root, current, expr, summary_only=False):
  if expr:
    joined = '.'.join([current, expr])
  else:
    joined = current
#  print('running jsonpath query: "{}"'.format(joined))
  jsonpath_expr = parse(joined)
  match = jsonpath_expr.find(root)
  if not match:
    raise IJsonEdException('Jsonpath expression {} has no match'.format(joined))
  for curr in match:
    if summary_only:
      if type(curr.value) == dict:
        for key in sorted(curr.value.keys()):
          print(key)
      elif type(curr.value) == list:
        if not curr.value:
          print('[]')
        else:
          print('[0..{}]'.format(len(curr.value) - 1))
      else:
        print(curr.value)
    else:
      print(json.dumps(curr.value, sort_keys=True, indent=4, separators=(',', ': ')))


def modify(root, current, expr, new_value):
  new_root = deepcopy(root)

  if expr == '.':
    joined = current
  else:
    joined = '.'.join([current, expr])

  jsonpath_expr = parse(joined)
  match = jsonpath_expr.find(root)
  if not match:
    raise IJsonEdException('Jsonpath expression {} has no match'.format(joined))
  for curr in match:
    path = str(curr.full_path)
    node = new_root
    for sub_path in path.split('.')[:-1]:
      if sub_path.startswith('['):
        index = int(sub_path.lstrip('[').rstrip(']'))
      else:
        index = sub_path
      node = node[index]
    node[path.split('.')[-1]] = value_parse(new_value)

  return new_root


def value_parse(val):
  if val.startswith('"'):
    return val.strip('"')
  elif val == 'true':
    return True
  elif val == 'false':
    return False
  else:
    try:
      return float(val)
    except:
      return val


if __name__ == '__main__':
  main()
