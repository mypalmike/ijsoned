# ijsoned

Interactive JSON editor.

## Installation

It's usually best to do this in a virtual environment.

```
pip install ijsoned
```

## Features

- Navigate a json structure like a file system, using jsonpath.
- View fields or entire structure at current level.
- Tab completion.
- History (up arrow, ctrl-r) per session.
- Change values.
- Commit to save.

## Future goals

- Unset functionality, to remove data from the document.
- Add json syntax highlighting to the show command
- Add json schema functionality for both validation and improved tab completion.

## Known issues

- Error messages are often not terribly helpful at the moment.
- Use of jsonpath is not consistent. For example, `show $.foo.bar` shows the document starting from the root, but `set $.foo.bar (value)` creates a "$" key in the current location.

If you find the software useful and want to see it improved, file a bug report. Or better yet, make the code changes and submit a pull request.

## Example session

Let's say we want to edit the following json file, blog.json (from https://json-schema.org/learn/json-schema-examples)

```json
{
  "title": "New Blog Post",
  "content": "This is the content of the blog post...",
  "publishedDate": "2023-08-25T15:00:00Z",
  "author": {
    "username": "authoruser",
    "email": "author@example.com"
  },
  "tags": ["Technology", "Programming"]
}
```

Open the json file like so:

```text
$ ijsoned blog.json
IJsonEd. Type help or ? to list commands.
$>
```

The $ is the root of a jsonpath path, which is where you start editing.

### The help or ? command

Gives very brief help.

```text
$> help

Documented commands (type help <topic>):
========================================
EOF  cd  commit  diff  exit  help  pwd  set  show  summary  top  up

$> ? diff
Display a diff between the current json and the most recent commit
```

### The show command

By itself, the show command displays the json at the current location.

```text
$> show
{
    "author": {
        "email": "author@example.com",
        "username": "authoruser"
    },
    "content": "This is the content of the blog post...",
    "publishedDate": "2023-08-25T15:00:00Z",
    "tags": [
        "Technology",
        "Programming"
    ],
    "title": "New Blog Post"
}
```

Using show followed by a jsonpath gets you the json result from that query.

```text
$> show author
{
    "email": "author@example.com",
    "username": "authoruser"
}
```

### The summary command

The summary command shows one level of keys. Like show, it can be used alone or with a jsonpath.

```text
$> summary
author
content
publishedDate
tags
title
$> summary title
New Blog Post
$> summary tags
[0..1]

```

### Location commands: cd, top, up, pwd

These commands allow you to navigate to locations within the json document, allowing you to focus on a subset of the document more easily.

```
$> pwd
$
$> cd tags
tags> show
[
    "Technology",
    "Programming"
]
tags> up
$> cd <typing the tab key reveals the following completions...>
author         content        publishedDate  tags           title
$> cd author
author> pwd
author
```

### The set command

The set command lets you modify or add to the json document. Here are some examples:

```text
tags> cd $.author
author> show
{
    "email": "author@example.com",
    "username": "authoruser"
}
author> set username "newusername"
author> set nickname "Rick"
author> show
{
    "email": "author@example.com",
    "nickname": "Rick",
    "username": "newusername"
}
```

You can set arbitrary JSON values.

```text
$> cd author
author> set education {"university": "University of Hard Knocks", "GPA": 4.0}
author> show
{
    "education": {
        "GPA": 4.0,
        "university": "University of Hard Knocks"
    },
    "email": "author@example.com",
    "username": "authoruser"
}
```

You can create deep structures by specifying them in jsonpath.

```text
$> set a.b.c.d "Created deep structure"
$> show a
{
    "b": {
        "c": {
            "d": "Created deep structure"
        }
    }
}
```

Similarly, you can add an index beyond a current array size and it will expand the array for you.

```text
$> set tags[5] "History"
$> show tags
[
    "Technology",
    "Programming",
    null,
    null,
    null,
    "History"
]
```

### The diff command

The diff command shows you what has changed in the document. This command always shows the diff at the root level. Note that the line numbers are based on how ijsoned formats text, and may not match the source file.

```text
$> set author. < tab completion shows the next level down >
author.email     author.username
$> set author.email "different_user@example.com"
$> diff
--- orig
+++ current
@@ -1,6 +1,6 @@
 {
     "author": {
-        "email": "author@example.com",
+        "email": "different_user@example.com",
         "username": "authoruser"
     },
     "content": "This is the content of the blog post...",
```

### The commit command

The commit command saves the file. It overwrites the input file and does not make any attempt to back up the original, so if you need to do that, do it before launching ijsoned. After the commit, the diff command will show no differences.

```text
$> diff
--- orig
+++ current
@@ -1,6 +1,6 @@
 {
     "author": {
-        "email": "author@example.com",
+        "email": "different_user@example.com",
         "username": "authoruser"
     },
     "content": "This is the content of the blog post...",

$> commit
$> diff

$>
```
