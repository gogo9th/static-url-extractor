from typing import NewType
from typing import Optional, List, Tuple
# import collections
import attr


__all__ = ['URLString', 'PathString', 'MimeTypeString', 'WebResponse']


URLString = NewType('URLString', str)
PathString = NewType('PathString', str)
MimeTypeString = NewType('MimeTypeString', str)

# WebResponse = collections.namedtuple('WebResponse', ['status_code', 'headers', 'encoding', 'text'])

WebResponse = attr.make_class('WebResponse', {
    'url': attr.ib(type=Optional[URLString], default=None),
    'status_code': attr.ib(type=Optional[int], default=None),
    'reason': attr.ib(type=str, default=''),
    'ok': attr.ib(type=Optional[bool], default=True),
    'headers': attr.ib(type=List[Tuple[str, str]], default=None),
    'cookies': attr.ib(type=List[Tuple[str, str]], default=None),
    'encoding': attr.ib(type=Optional[str], default=None),
    'content': attr.ib(type=Optional[bytes], default=None),
    'text': attr.ib(type=Optional[str], default=None),
})


# EOF
