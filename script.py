from typing import Iterable
from bs4 import BeautifulSoup
import utils
from newtypes import URLString
from glue import ResourceLoader
import json
import bs4.element
import requests


__all__ = ['pick_src', 'find_external_scripts', 'embed_all']



def pick_url(tag_element: bs4.element.Tag) -> URLString:
    return URLString(tag_element.attrs['url'])

def pick_src(tag_element: bs4.element.Tag) -> URLString:
    '''
    TAG에서 `src` 속성 추출
    @param script_element: TAG
    @return: 추출한 `src` 속성 값
    '''
    return URLString(tag_element.attrs['src'])


def find_external_scripts(html_tree: BeautifulSoup) -> Iterable[bs4.element.Tag]:
    '''
    HTML 트리에서 external script 요소 탐색
    @param html_tree: HTML 트리
    @return: external script 요소에 대한 이터레이터
    '''

    for script_element in html_tree.find_all('script'):
        if 'src' not in script_element.attrs:
            continue
        #print ("Found Script Tag: " + str(script_element.attrs))
        yield script_element


def embed(script_element: bs4.element.Tag, code: str) -> bs4.element.Tag:
    '''
    external script 요소를 embeded script 요소로 바꿉니다.
    @param script_element: external script 요소
    @param code: 스크립트 코드
    @return: embeded script 요소
    '''

    script_element.clear()
    script_element.append(code)

    if 'src' in script_element.attrs:
        del script_element.attrs['src']

    return script_element


def embed_all(html_tree: BeautifulSoup, loader: ResourceLoader) -> BeautifulSoup:
    '''
    HTML 트리의 external script 요소를 모두 embeded script 요소로 바꿉니다.
    @param html_tree: HTML 트리
    @param loader: pyproxy.glue.ResourceLoader 오브젝트
    @return: HTML 트리
    '''
    embed_url = []
    for script_element in find_external_scripts(html_tree):
        try:
            src = pick_src(script_element)

            response = loader.load_in_response(src)

            comments = utils.js_comment(
                f'src = {src}\n'
                f'status_code: {response.status_code}\n'
                f'reason: {response.reason}\n'
                f'encoding: {response.encoding}\n'
                f'{json.dumps(response.headers, indent=2)}\n'
            )
            embed_url.append(src)

            # UTF-8로 대동단결!

            if response.ok:
                code = f'{comments}\n{response.text}\n'
            else:
                code = f'{comments}\n{utils.js_comment(response.text)}\n'

        except requests.exceptions.ConnectionError as ex:
            comments = utils.js_comment(f'src = {src}\n{ex}\n')
            code = comments

        except requests.exceptions.ReadTimeout as ex:
            comments = utils.js_comment(f'src = {src}\n{ex}\n')
            code = comments

        script_element = embed(script_element, code)

    return html_tree,embed_url


# EOF
