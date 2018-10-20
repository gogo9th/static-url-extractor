from typing import Iterable
from bs4 import BeautifulSoup
from newtypes import URLString
from glue import ResourceLoader
import bs4.element


__all__ = ['check_to_stylesheet', 'pick_href', 'find_external_stylesheets', 'embed_all']


def check_to_stylesheet(link: bs4.element.Tag) -> bool:
    '''
    <link> 요소가 스타일시트와 연결되어 있는지 검사
    @param link: <link> 요소
    @return: <link> 요소가 스타일시트와 연결되어 있으면 참
    '''

    if 'rel' not in link.attrs:
        return False

    if 'stylesheet' in link.attrs['rel']:
        return True
    else:
        return False


def check_to_icon(link: bs4.element.Tag) -> bool:
    '''
    <link> 요소가 스타일시트와 연결되어 있는지 검사
    @param link: <link> 요소
    @return: <link> 요소가 스타일시트와 연결되어 있으면 참
    '''

    if 'rel' not in link.attrs:
        return False

    if 'icon' in link.attrs['rel']:
        return True
    else:
        return False


def pick_href(element: bs4.element.Tag) -> URLString:
    '''
    HTML 요소에서 `href` 속성 추출
    @param element: HTML 요소
    @return: 추출한 `href` 속성 값
    '''
    return URLString(element.attrs['href'])


def find_external_stylesheets(html_tree: BeautifulSoup) -> Iterable[bs4.element.Tag]:
    '''
    HTML 트리에서 external style 요소(<link>) 탐색
    @param html_tree: HTML 트리
    @return: external style 요소에 대한 이터레이터
    '''

    for link_tag in html_tree.find_all('link'):
        if not check_to_stylesheet(link_tag):
            continue
        if 'href' not in link_tag.attrs:
            continue
        yield link_tag


def find_external_icons(html_tree: BeautifulSoup) -> Iterable[bs4.element.Tag]:
    '''
    HTML 트리에서 external style 요소(<link>) 탐색
    @param html_tree: HTML 트리
    @return: external style 요소에 대한 이터레이터
    '''

    for link_tag in html_tree.find_all('link'):
        if not check_to_icon(link_tag):
            continue
        if 'href' not in link_tag.attrs:
            continue
        yield link_tag

def find_meta_urls(html_tree: BeautifulSoup) -> Iterable[bs4.element.Tag]:

    for meta_tag in html_tree.find_all('meta'):
        if 'url' not in meta_tag.attrs:
            continue
        yield meta_tag

def find_srcs(html_tree: BeautifulSoup) -> Iterable[bs4.element.Tag]:

#    for img_tag in html_tree.find_all('img'):
#        print ("Image: " + str(img_tag))

    #for img_tag in html_tree.find_all('img'):
    for tag in html_tree.find_all():
        #print("Tag Name: " + str(tag))
        if 'src' not in tag.attrs:
            continue
        #print ("Source: " + str(tag))
        yield tag


def embed(element: bs4.element.Tag, stylesheet: str) -> bs4.element.Tag:
    '''
    external style 요소(<link>)를 embeded style 요소(<style>)로 바꿉니다.
    @param element: external style 요소
    @param stylesheet: 스타일시트
    @return: embeded style 요소
    '''

    element.clear()
    element.append(stylesheet)
    element.name = 'style'

    if 'rel' in element.attrs:
        del element.attrs['rel']
    if 'href' in element.attrs:
        del element.attrs['href']

    return element


def embed_all(html_tree: BeautifulSoup, loader: ResourceLoader) -> BeautifulSoup:
    '''
    HTML 트리의 external style 요소(<link>)를 모두 embeded style 요소(<style>)로 바꿉니다.
    @param html_tree: HTML 트리
    @param loader: pyproxy.glue.ResourceLoader 오브젝트
    @return: HTML 트리
    '''

    for link_tag in find_external_stylesheets(html_tree):
        href = pick_href(link_tag)

        # UTF-8로 대동단결!
        stylesheet = loader.load(href)

        style_tag = embed(link_tag, stylesheet)  # noqa: F841

    return html_tree


# EOF
