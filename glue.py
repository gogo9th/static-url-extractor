import os.path
import random
import time
import sys
import json

import attr
import requests

from typing import Optional, Union, Any, Tuple, List, Dict, Callable
from urllib.parse import urlparse, urlunparse
from pathlib import Path
from newtypes import PathString, URLString, WebResponse
import requests, urllib, requests
import socket
import ssl
import json


__all__ = [
    'ResourceLoader',
    'LocalResourceLoader',
    'RemoteResourceLoader',
    'ResourceURLResolver',
    'OutputPathResolver',
]


class ResourceLoader:
    '''리소스 내용을 가져옵니다.'''

    def load(self, url: URLString) -> str:
        '''
        리소스 내용을 가져옵니다.
        @param url: 리소스 주소
        @return: 리소스 내용
        '''
        loader, args, kwargs = self.prepare(url)
        result = loader(*args, **kwargs)
        return result

    def load_in_response(self, url: URLString) -> WebResponse:
        '''
        리소스 내용을 가져옵니다.
        @param url: 리소스 주소
        @return: `WebResponse` 객체
        '''
        loader, args, kwargs = self.plan(url)
        result = loader(*args, **kwargs)
        return result

    @staticmethod
    def select_random_user_agent() -> str:

        # 그러한 날이 있소.
        # 정직한 마음으로 'python-requests'로서 다가갔지만 웹 서버에게 차별을 받는 날이.
        #
        # 그러므로 웹 서버에게 나는,
        #
        # "친애하는 서버여,
        # 나는 크롬의 64번째 모습, 웹킷의 자손, KHTML의 후예,
        # 겍코를 따르는 자, 위대한 모질라 5.0의 추종자로서
        # 윈도 NT 10에서 실행되고 있다."
        #
        # 같은 사기를 쳐서라도 차별에서 벗어나고자 하오.

        agents = {
"Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/69.0.3497.81 Chrome/69.0.3497.81 Safari/537.36"
        }

        result = random.choice([*agents])
        return result

    @staticmethod
    def read_file(path: Path) -> str:
        '''
        파일을 읽어 리소스 내용을 가져옵니다.
        @param path: 리소스 파일 경로
        @return: 리소스 내용
        '''
        result = path.read_text()
        return result

    @classmethod
    def read_file_in_response(cls, path: Path) -> WebResponse:
        '''
        파일을 읽어 리소스 내용을 가져옵니다.
        @param path: 리소스 파일 경로
        @return: `WebResponse` 객체
        '''
        result = WebResponse(text=cls.read_file(path))
        return result

    #: 다운로드 실패 시 재시도 회수 기본값
    DEFAULT_DOWNLOAD_RETRY: int = 8
    # DEFAULT_DOWNLOAD_RETRY: int = 32

    #: 다운로드 실패 시 재시도 지연(초) 기본값
    DEFAULT_DOWNLOAD_RETRY_DELAY_SEC: float = 0.3

    DEFAULT_DOWNLOAD_TIMEOUT: float = 10

    @classmethod
    def get(cls, url, retry=DEFAULT_DOWNLOAD_RETRY, retry_delay_sec=DEFAULT_DOWNLOAD_RETRY_DELAY_SEC, timeout=DEFAULT_DOWNLOAD_TIMEOUT) -> WebResponse:
        '''
        네트워크에서 리소스 내용을 다운로드합니다.
        @param path: 리소스 주소
        @param retry: 실패 시 재시도 회수
        @return: `WebResponse` 객체
        '''

        while True:
            req = requests.Session()
            try:

                request_headers = {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'Accept-Encoding': 'deflate',
                    'User-Agent': cls.select_random_user_agent(),
                }

                print(f'Loading... {url}', file=sys.stderr)
                print(json.dumps(request_headers, indent=2), file=sys.stderr)

                response = req.get(
                    url,
                    stream=True,
                    verify=False,
                    timeout=timeout,
                    headers=request_headers,
                    allow_redirects=True
                )

                result = WebResponse(
                    url=url,
                    status_code=response.status_code,
                    reason=response.reason,
                    ok=response.ok,
                    headers=[*response.headers.items()],
                    cookies=[*response.cookies.items()],
                    encoding=response.encoding,
                    content=response.content,
                )

                response.encoding = response.encoding or 'utf-8'
                result.text = response.text

                print(
                    f'src = {url}\n'
                    f'status_code: {result.status_code}\n'
                    f'reason: {result.reason}\n'
                    f'encoding: {result.encoding}\n'
                    f'{json.dumps(result.headers, indent=2)}\n',
                    file=sys.stderr
                )

                if response.ok or retry <= 0:
                    req.close()
                    return result
                else:
                    if response:
                        req.close()
            except requests.exceptions.ConnectionError as ex:
                print(ex, file=sys.stderr)
                if retry <= 0:
                    if response:
                        req.close()
                    raise

            except requests.exceptions.ContentDecodingError as ex:
                print(ex, file=sys.stderr)
                if retry <= 0:
                    if response:
                        req.close()
                    raise

            except requests.exceptions.ReadTimeout as ex:
                print(ex, file=sys.stderr)
                if retry <= 0:
                    if response:
                        req.close()
                    raise

            time.sleep(retry_delay_sec)
            retry -= 1

    @classmethod
    def download(cls, url: URLString, retry: int = DEFAULT_DOWNLOAD_RETRY) -> str:
        #####print ("Download : " + str(url))
        '''
        네트워크에서 리소스 내용을 다운로드합니다.
        @param path: 리소스 주소
        @param retry: 실패 시 재시도 회수
        @return: 리소스 내용
        '''
        result = cls.get(url, retry).text
        return result


class LocalResourceLoader(ResourceLoader):
    '''리소스 내용을 가져옵니다.'''

    #: 마크업 디렉토리 경로
    __markup_dir: Optional[Path] = None

    @property
    def markup_dir(self) -> Optional[Path]:
        return self.__markup_dir

    @markup_dir.setter
    def markup_dir(self, value: Optional[Union[Path, PathString]]):
        if value is None:
            self.__markup_dir = None
            return
        self.__markup_dir = Path(value)

    #: 웹 사이트 루트 경로
    __webroot: Optional[Path] = None

    @property
    def webroot(self) -> Optional[Path]:
        if self.__webroot is None:
            return self.markup_dir
        return self.__webroot

    @webroot.setter
    def webroot(self, value: Optional[Union[Path, PathString]]):
        if value is None:
            self.__webroot = None
            return
        self.__webroot = Path(value)

    #: URL 기본 스킴
    default_scheme: Optional[str] = None  # noqa: E704

    def prepare(self, url: URLString) -> Tuple[Callable[..., str], List[Any], Dict[str, Any]]:
        '''
        URL을 분석하여 리소스 내용을 가져올 준비를 합니다.
        @param url: 리소스 주소
        @return: (callable loader, args, kwargs)
        '''

        url_parts = urlparse(url)
        result = (None, [], {})

        if url_parts.scheme == '' and url_parts.netloc == '':
            vpath = url_parts.path
            syspath = None

            if os.path.isabs(vpath):
                # 절대 경로인 경우
                syspath = self.webroot / os.path.relpath(vpath, '/')
            else:
                # 상대 경로인 경우
                syspath = self.markup_dir / vpath

            result = (self.read_file, [syspath], {})

        else:
            # external URL인 경우
            if url_parts.scheme == '':
                absolute_url = urlunparse([self.default_scheme, *url_parts[1:]])
            else:
                absolute_url = url

            result = (self.download, [absolute_url], {})

        return result

    def plan(self, url: URLString) -> Tuple[Callable[..., WebResponse], List[Any], Dict[str, Any]]:
        '''
        URL을 분석하여 리소스 내용을 가져올 준비를 합니다.
        @param url: 리소스 주소
        @return: (callable loader, args, kwargs)
        '''

        url_parts = urlparse(url)
        result = (None, [], {})

        if url_parts.scheme == '' and url_parts.netloc == '':
            vpath = url_parts.path
            syspath = None

            if os.path.isabs(vpath):
                # 절대 경로인 경우
                syspath = self.webroot / os.path.relpath(vpath, '/')
            else:
                # 상대 경로인 경우
                syspath = self.markup_dir / vpath

            result = (self.read_file_in_response, [syspath], {})

        else:
            # external URL인 경우
            if url_parts.scheme == '':
                absolute_url = urlunparse([self.default_scheme, *url_parts[1:]])
            else:
                absolute_url = url

            result = (self.get, [absolute_url], {})

        return result


@attr.s
class RemoteResourceLoader(ResourceLoader):
    '''리소스 내용을 가져옵니다.'''

    _base_url: URLString = attr.ib()

    def prepare(self, url: URLString) -> Tuple[Callable[..., str], List[Any], Dict[str, Any]]:
        '''
        URL을 분석하여 리소스 내용을 가져올 준비를 합니다.
        @param url: 리소스 주소
        @return: (callable loader, args, kwargs)
        '''
        resolver = ResourceURLResolver(self._base_url)
        resolver.resource_url = url
        result = (ResourceLoader.download, [resolver.resource_url], {})
        return result

    def plan(self, url: URLString) -> Tuple[Callable[..., WebResponse], List[Any], Dict[str, Any]]:
        '''
        URL을 분석하여 리소스 내용을 가져올 준비를 합니다.
        @param url: 리소스 주소
        @return: (callable loader, args, kwargs)
        '''
        resolver = ResourceURLResolver(self._base_url)
        resolver.resource_url = url
        result = (ResourceLoader.get, [resolver.resource_url], {})
        return result


@attr.s
class ResourceURLResolver:
    base_url: URLString = attr.ib()

    #: 리소스 URL
    __resource_url: URLString = ''

    @property
    def resource_url(self) -> URLString:
        base_parts = urlparse(self.base_url)
        resource_parts = urlparse(self.__resource_url)

        scheme = resource_parts.scheme or base_parts.scheme or 'http'

        if resource_parts.netloc:
            netloc = resource_parts.netloc
            path = resource_parts.path

        else:
            netloc = base_parts.netloc

            if os.path.isabs(resource_parts.path):
                path = resource_parts.path
            else:
                path = os.path.join(os.path.dirname(base_parts.path), resource_parts.path)

        params, query, fragment = resource_parts[3:]

        result = urlunparse((scheme, netloc, path, params, query, fragment))
        return result

    @resource_url.setter
    def resource_url(self, value: URLString):
        self.__resource_url = value


@attr.s
class OutputPathResolver(ResourceURLResolver):
    _webroot: Path = attr.ib(converter=Path)

    #: 기본 파일 이름
    default_basename: str = 'index.html'  # noqa: E704

    @property
    def output_dir(self) -> Optional[Path]:
        parts = urlparse(self.resource_url)

        if parts.netloc != urlparse(self.base_url).netloc:
            return None

        acc = self._webroot

        if os.path.isabs(parts.path):
            acc /= os.path.relpath(os.path.dirname(parts.path), '/')
        else:
            acc /= parts.path

        return acc

    @property
    def output_path(self) -> Optional[Path]:
        if self.output_dir is None:
            return None

        basename = os.path.basename(urlparse(self.resource_url).path) or self.default_basename
        result = self.output_dir / basename
        return result


def fill_url_scheme(url: URLString, scheme: int) -> URLString:
    parts = urlparse(url)
    
    if parts.netloc == '':
        if(scheme == 1):
            result = "https://"+url
        else:
            result = "http://"+url
    else:
        result = url
    return result

# def fill_url_scheme_(url: URLString, args: str, scheme: str = 'http') -> URLString:

def fill_url_scheme_(url: URLString, args: str, scheme: int) -> URLString:
    parts = urlparse(url)
    if (parts.netloc == '' and parts.scheme == ''):
        result = f'{args}{url}'
        return result

    elif (parts.scheme == ''):
        result = f'{url.replace("//","")}'
        if(scheme == 1):
            result = "https://"+result
        else:
            result = "http://"+result
        return result

    else:
        result = urlunparse(parts)
        return result


def getcert(addr, timeout=3):    
    try:
        with socket.create_connection((addr,443), timeout=timeout) as sock:
            context = ssl.create_default_context()
            with context.wrap_socket(sock, server_hostname=addr) as sslsock:
                print(f'SSL/TLS Flag : ' + json.dumps(sslsock.getpeercert()),file=sys.stderr)
                return 1
    except socket.timeout as e:
        return 0
    except Exception as e:
        return 0
