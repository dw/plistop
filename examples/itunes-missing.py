"""
Given a folder structure like:
    "~/Music/CDs/<Artist> - <Album>/<NN> - <Title>"

Deal with iTunes idiocy in losing track of its files, especially across
backup/restore.

Finds all paths not in the library and fuzzy matches them against titles in the
library that are missing.
"""

import os
import re
import string
import urllib
import urlparse

import plistop
import unidecode


def tformat(t):
    s = u'%s: %s: %s (%s)' % (t.get('Artist'),
                              t.get('Album'),
                              t.get('Name'),
                              t.get('Track ID'))
    return s.encode('utf-8')


kill1 = '&,():_[]/%=@-'
kill2 = ' ' * len(kill1)
delete = '.?\''

TRANS = string.maketrans(kill1, kill2)
def tokenize(s):
    if type(s) is str:
        s = s.decode('utf-8')
    s = unidecode.unidecode(s).encode('ascii')
    raw = s.translate(TRANS, delete).lower().split()
    return {r for r in raw if not r.isdigit()}


home_dir = os.path.expanduser('~')
music_dir = os.path.join(home_dir, 'Music')
path = os.path.join(music_dir, 'iTunes Music Library.xml')


with open(path) as fp:
    lib = plistop.parse(fp)


# set of duplicate track IDs.
dups = set()
files = {}
# set of existent paths found in library
seen = set()
# dirpath -> list of (track ID, filename)
missing_by_dir = {}

for idx, track in enumerate(lib['Tracks'].itervalues()):
    url = track['Location']
    if url in files:
        dups.add(track['Track ID'])
    else:
        files[url] = track

        parsed = urlparse.urlparse(url)
        if parsed.scheme == 'file':
            path = urllib.unquote(parsed.path)
            if os.path.exists(path):
                seen.add(path)
            else:
                dirname = os.path.dirname(path)
                missing_by_dir.setdefault(dirname, [])\
                    .append((track['Track ID'], path))


# token -> number of appearences anywhere
tfreq = {}
# dirpath -> set of tokens in dir
dirtoks = {}
# token -> list of dirs containing token
tokpath = {}


for dirpath, dirnames, filenames in os.walk(music_dir + '/CDs'):
    dirtok = set()
    for filename in filenames:
        path = os.path.join(dirpath, filename)
        if path not in seen:
            root, ext = os.path.splitext(filename)
            ftoks = tokenize(root)
            for tok in ftoks:
                tfreq[tok] = tfreq.get(tok, 0) + 1
            dirtok.update(ftoks)
    if dirtok:
        dirtoks[dirpath] = dirtok
        for tok in dirtok:
            tokpath.setdefault(tok, []).append(dirpath)


for dirname, pairs in missing_by_dir.iteritems():
    for track_id, path in pairs:
        path = os.path.relpath(path, home_dir)
        track = lib['Tracks'][track_id]
        print
        print '???', tformat(track), repr(path)
        root, ext = os.path.splitext(os.path.basename(path))
        for k in sorted(tokenize(root), key=tfreq.get):
            mtokpaths = tokpath.get(k)
            if mtokpaths:
                print k, mtokpaths
        print
