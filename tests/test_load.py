import plistop
import plistlib


def compare(a, b):
    if isinstance(a, (plistop.PListDict, dict)):
        assert set(a.keys()) == set(b.keys())
        for k, v in a.iteritems():
            compare(v, b[k])
    elif isinstance(a, (plistop.PListArray, list)):
        assert len(a) == len(b)
        for elemA, elemB in zip(a, b):
            compare(elemA, elemB)
    elif isinstance(a, (bool, int, float, str, bytes)):
        assert a == b
    else:
        assert False


def test_loading_from_proplib():
    filename = 'tests/props.plist'
    a = plistop.parse(open(filename))
    b = plistlib.load(open(filename, 'rb'), fmt=plistlib.FMT_XML)
    compare(a, b)
