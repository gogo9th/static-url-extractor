from newtypes import MimeTypeString
from bs4 import BeautifulSoup
import sys
import re


__all__ = ['grow_recursion_limit', 'flat', 'js_comment', 'StreamPrinter']


def grow_recursion_limit(limit) -> None:
    '''
    재귀 한계를 키웁니다. 목표 한계가 현재 한계보다 작아도 재귀 한계가 작아지지 않습니다.
    @param limit: 목표 한계
    '''
    sys.setrecursionlimit(max(sys.getrecursionlimit(), limit))


def flat(html_tree: BeautifulSoup, tag_name: str) -> BeautifulSoup:
    for tag in html_tree.find_all(tag_name):
        for child in reversed([*tag]):
            tag.insert_after(child)
    return html_tree


def js_comment(lines: str) -> str:
    result = lines
    result = re.sub(r'^', '// ', result)
    result = re.sub(r'\n', '\n// ', result)
    return result


def get_suffix(mime_type: MimeTypeString) -> str:
    '''
    @param mime_type: MIME 타입
    @return: suffix
    '''

    suffix_to_mime_type_table = {
        ".html": [
            "text/html",
        ],
        ".css": [
            "text/css",
        ],
        ".js": [
            "application/ecmascript",
            "application/javascript",
            "application/js",
            "application/x-javascript",
            "text/ecmascript",
            "text/javascript",
        ],
    }

    mime_type_to_suffix_table = {
        mime_type: suffix
        for suffix, mime_types in suffix_to_mime_type_table.items()
        for mime_type in mime_types
    }

    return mime_type_to_suffix_table[mime_type]


# FIXME: `attr` 모듈을 쓰면 더 예뻐집니다.
class StreamPrinter:
    def __init__(self, stream: object):
        self.stream = stream

    def print(self, *args, **kwargs) -> None:
        '''스트림으로 print'''
        print(file=self.stream, flush=True, *args, **kwargs)


# EOF
