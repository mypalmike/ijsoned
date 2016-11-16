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

  def __init__(self, filename, path):
    cmd.Cmd.__init__(self)

    doc = {}
    try:
      with open(filename) as f_in:
        doc = json.load(f_in)
    except:
      pass  # New file

    self.filename = filename
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
      expr, new_value = arg.split(None, 1)
      self.doc = modify(self.doc, self.path, expr, new_value)
    except Exception as error:
      self.dump_error(error)

  def do_commit(self, arg):
    with open(self.filename, 'w') as f_out:
      json.dump(self.doc, f_out, sort_keys=True, indent=4, separators=(',', ': '))

  def do_exit(self, arg):
    """Exit ijsoned"""
    return True

  def do_EOF(self, arg):
    """EOF (ctrl-D) hook for exit"""
    print('exit')
    return True

  def dump_error(self, error):
    print(error, file=sys.stderr)

  def emptyline(self):
    pass

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
  if len(argv) != 2:
    print('Usage: ijsoned [filename]')
    return 1

  filename = argv[1]
  IJsonEd(filename, '$').cmdloop()


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
  val = value_parse(new_value)

  if expr == '.':
    joined = current
  else:
    joined = '.'.join([current, expr])

  if joined.startswith('$.'):
    joined = joined[2:]

  new_obj = build_object(joined, val)
  merged = merge_objects(root, new_obj)
  cleaned = replace_placeholders(merged)

  return cleaned


def value_parse(val):
  return json.loads(val)


OBJ_PLACEHOLDER = object()


def replace_placeholders(obj):
  typ = type(obj)

  if typ is dict:
    result = {}
    for key, val in obj.items():
      result[key] = replace_placeholders(val)
    return result

  if typ is list:
    result = [None] * len(obj)
    for idx, val in enumerate(obj):
      result[idx] = replace_placeholders(val)
    return result

  if obj is OBJ_PLACEHOLDER:
    return None

  return obj


def merge_objects(obj1, obj2):
  """
  Given two json-serializable objects, merge into a result object.

  """
  type1 = type(obj1)
  type2 = type(obj2)

  if type1 is dict and type2 is dict:
    result = {}
    keys1 = set(obj1.keys())
    keys2 = set(obj2.keys())
    keep1 = keys1 - keys2
    keep2 = keys2 - keys1
    shared = keys1 & keys2

    for key in keep1:
      result[key] = obj1[key]

    for key in keep2:
      result[key] = obj2[key]

    for key in shared:
      result[key] = merge_objects(obj1[key], obj2[key])

    return result

  if type1 is list and type2 is list:
    total_len = max(len(obj1), len(obj2))
    result = [OBJ_PLACEHOLDER] * total_len
    for idx in range(total_len):
      # TODO FIX
      result[idx] = merge_objects(obj1[idx], obj2[idx])
    return result

  if obj2 is OBJ_PLACEHOLDER:
    return obj1

  return obj2


def build_object(expr, val):
  """
  Recursively build a (potentially) deep, json-serializable object that encapsulates
  one value. Format for expr is a subset of jsonpath with dot notation for keys, parens
  for lists. e.g. build_object(expr="foo.bar[3].baz", val="hello") results in
  the object:

  {'foo': {'bar': [None, None, None, {'baz': 5}]}}

  Implementation is recursive right-to-left parser.

  """
  if not expr:
    return val

  # Parse list
  if expr[-1] == ']':
    remainder, list_index = expr.rsplit('[')
    remainder = remainder.rstrip('.')
    list_index = list_index[:-1]
    list_index = int(list_index)
    new_list = [OBJ_PLACEHOLDER] * (list_index + 1)
    new_list[list_index] = val
    return build_object(remainder, new_list)

  # Parse dict
  idx_dot = expr.rfind('.')
  if idx_dot == -1:
    return {expr: val}
  else:
    remainder, current = expr.rsplit('.', 1)
    return build_object(remainder, {current: val})


if __name__ == '__main__':
  main()
