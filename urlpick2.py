import requests
import tinycss2
import urllib
from urllib.request import urlopen

from argparse import ArgumentParser
from signal import signal, SIGPIPE, SIG_DFL
from bs4 import BeautifulSoup
import pyproxy.urlsearch.static as static_url


if __name__ == '__main__':
	arg_parser = ArgumentParser(description='Pick URLs out of a URL')

	arg_parser.add_argument('html_url', metavar='URL(.html)', help='URL address')
	#arg_parser.add_argument('html_filename', metavar='FILE', help='filename of web page')
	args = arg_parser.parse_args()

	signal(SIGPIPE, SIG_DFL)

	if (args.html_url.find(":") == -1):
		args.html_url = "http://" + args.html_url

	r = requests.get(args.html_url)
	pageURL = r.url
	print(pageURL)



def CCS_Find_Resources(ccs_url):

   urlDictionary = {}
   response = urlopen(ccs_url)

   # print(response)
   # print(response.info())
   # print(response.info().get_content_type())

   rules, encoding = tinycss2.parse_stylesheet_bytes(css_bytes=response.read()#,
   # Python 3.x
   #protocol_encoding=response.info().get_content_type().get_param('charset'),
   # Python 2.x
   #protocol_encoding=response.info().gettype().getparam('charset'),
   )

   for rule in rules:
      contents = '';
      if (isinstance(rule, tinycss2.ast.QualifiedRule) or isinstance(rule, tinycss2.ast.AtRule)):
         contents = rule.content

         for token in contents:
            if (isinstance(token, tinycss2.ast.URLToken)):
               url = token.value
               if (len(url) >= 2 and url[0] == '/' and url[1] == '/'):
                  temp = url[2:]
                  url = temp
               elif (url.find(':') == -1):
                  temp = pageURL + url
                  url = temp

               if (url not in urlDictionary):
                  urlDictionary[url] = url
                  print(url)

