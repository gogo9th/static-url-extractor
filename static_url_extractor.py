#!/usr/bin/env python


'''
Automatic Test

1. Download the web document
2. Anlalyze the web document.
3. Download scripts connected to the web document.
4. Download style sheets connected to the web document.
'''


import itertools
import script as script_search
import style as style_search

from argparse import Namespace, ArgumentParser
from pathlib import Path
from copy import deepcopy
from signal import signal, SIGPIPE, SIG_DFL
from bs4 import BeautifulSoup
from glue import fill_url_scheme, OutputPathResolver, ResourceLoader

import requests
import tinycss2
import urllib
from urllib.request import urlopen


markup_resolver = ''
pageURL = None
hostname = None
recursiveResourceList = []

allURLs = []
failedURLs = []
allResources = []
failedResources = []
levelCount = []

pureURLs = []

def parse_args(*args, **kwargs) -> Namespace:
    prsr = ArgumentParser(
        description='Auto download web document with linked, scripts and stylesheets')

    prsr.add_argument(
       'url', metavar='URL', help='address of web document')
    #prsr.add_argument(
    #    '-b', '--webroot',
    #    metavar='DIRECTORY', help='root directory of website', required=True, type=Path)

    result = prsr.parse_args(*args, **kwargs)
    return result

def ResolveURL(url):

    if (len(url) >= 2 and url[0] == '/' and url[1] != '/'):
        url = url[1:]

    if (len(url) >= 2 and url[0] == '/' and url[1] == '/'):
        temp = url[2:]
        url = "http://" + temp
                 
    if (len(url) >= 3 and url[0] == '.' and url[1] == '.' and url[2] == '/'):
        url = url[3:]

    if (url.find(':') == -1):
        temp = hostname
        if temp[len(temp)-1] != '/':
            temp = temp + '/'
        temp = temp + url
        url = temp
        #url = url.replace("https://", "http://")
    return url

def CCS_Find_Resources(resource_text):

    urlDictionary = {}
    rawUrlDictionary = {}
    global pageURL
    #print ("CCS pageURL2 = " + pageURL)
    ##resource_resolver = deepcopy(markup_resolver)
    ##resource_resolver.resource_url = ccs_url

    ##resource_text = ResourceLoader.download(resource_resolver.resource_url)
    #response = urlopen(ccs_url)

   # print(response)
   # print(response.info())
   # print(response.info().get_content_type())
    #print(resource_text)
    rules, encoding = tinycss2.parse_stylesheet_bytes(css_bytes=str.encode(resource_text))

    for rule in rules:
        contents = '';
        if (isinstance(rule, tinycss2.ast.QualifiedRule) or isinstance(rule, tinycss2.ast.AtRule)):
            contents = rule.content
        if contents == None:
            continue

        for token in contents:
            if (isinstance(token, tinycss2.ast.URLToken)):
                url = token.value
                url = url.strip()
                if (len(url) == 0):
                    continue
                url = ResolveURL(token.value)
                if (url not in urlDictionary):
                    urlDictionary[url] = url
                    rawUrlDictionary[url] = token.value
                    #print(url)
    return (urlDictionary, rawUrlDictionary)

                #resource_resolver = deepcopy(markup_resolver)
                #resource_resolver.resource_url = token.value
                #if resource_resolver.output_dir is None or resource_resolver.output_path is None:
                #    continue
                #print("Downloading " + resource_resolver.resource_url)
                #resource_text = ResourceLoader.download(resource_resolver.resource_url)
                #resource_resolver.output_dir.mkdir(parents=True, exist_ok=True)
                #resource_resolver.output_path.write_text(resource_text)



def main(args: Namespace) -> None:
    signal(SIGPIPE, SIG_DFL)

    count = 0
    prevCount = 0
    r = requests.get(args.url)
    #print (r.content)

    global pageURL
    global recursiveResourceList
    global allURLs
    global allResources
    global hostname
    allURLs.append((0, args.url, "None"))
    pureURLs.append(args.url)
    allResources.append((args.url))
    #levelCount.append(1)

    isFirst = True
    level = 1
    maxLevel = 1
    while (isFirst or len(recursiveResourceList) > 0):

        if (isFirst):
            pageURL = r.url
            level = 1
        else:
            elem = recursiveResourceList.pop()
            pageURL = elem[1]
            level = elem[0] + 1

        if maxLevel < level:
            maxLevel = level

        ###print ("Popped: " + pageURL)
        index = pageURL.find("://")

        index2 = pageURL[index+3:].find("/")
        hostname = pageURL[0:index + 3 + index2]
        scheme = ""
        ###print ("Hostname : " + str(hostname))
        if (hostname.find("http://") == 0):
            scheme = "http:"
        else:
            scheme = "https:"
        #if (index < 0):
        #    pageURL = hostname + pageURL
            #print("The URL is wrong: " + str(pageURL))
            #return
        #if (isFirst):
           #index2 = pageURL[index+3:].find("/")
           #hostname = pageURL[0:index + 3 + index2]
           #print ("Hostname : " + str(hostname))

        #if (pageURL[len(pageURL)-1] != '/'):
        #    pageURL = pageURL + '/'
        args.url = pageURL
        #####print ("pageURL = " + pageURL)

        #webroot = args.webroot.expanduser().resolve()
        global markup_resolver
        #print("Webroot: " + str(webroot))
        #markup_resolver = OutputPathResolver(fill_url_scheme(args.url, webroot), webroot)
        contents = ResourceLoader.download(pageURL)
        #print ("Contents:")
        #print (contents)

        if isFirst or pageURL.endswith(".html"):
            #print ("In " + pageURL)
            html_tree = BeautifulSoup(contents, features='html.parser')



            #markup_resolver.output_dir.mkdir(parents=True, exist_ok=True)

            # markup_resolver.output_path.write_text(html_tree.prettify())
            #markup_resolver.output_path.write_text(markup)

            ########## script_tags = script_search.find_external_scripts(html_tree)
            #####all_link_tags = style_search.find_external_import_links(html_tree)
            css_link_tags = style_search.find_external_stylesheets(html_tree)
            icon_link_tags = style_search.find_external_icons(html_tree)
            #img_tags = style_search.find_imgs(html_tree)
            src_tags = style_search.find_srcs(html_tree)
            url_meta_tags = style_search.find_meta_urls(html_tree)

            # Download all static URLs referenced by <script> and <link> tags
            # Download all static URLs sourced by <img> tags
            ########## script_url_iter = (script_search.pick_src(it) for it in script_tags)
            #####all_link_url_iter = (style_search.pick_href(it) for it in all_link_tags)
            css_link_url_iter = (style_search.pick_href(it) for it in css_link_tags)
            icon_link_url_iter = (style_search.pick_href(it) for it in icon_link_tags)
            url_meta_iter = (script_search.pick_url(it) for it in url_meta_tags)
            src_url_iter = (script_search.pick_src(it) for it in src_tags)
            #####resource_url_iter = itertools.chain(script_url_iter, all_link_url_iter, img_url_iter)
            resource_url_iter = itertools.chain(css_link_url_iter, icon_link_url_iter, url_meta_iter, src_url_iter)

            for resource_url in resource_url_iter:
                resource_url = resource_url.strip()
                if (resource_url == "about:blank") or resource_url[0:5] == "data:" or len(resource_url) == 0:
                     continue
                #resource_resolver = deepcopy(markup_resolver)
                #resource_resolver.resource_url = resource_url
                #if resource_resolver.output_dir is None or resource_resolver.output_path is None:
                #    continue
                #try:
                #    print ("Resource URL : " + resource_url)
                #    resource_resolver.output_dir.mkdir(parents=True, exist_ok=True)

                #except Exception as e:
                #    print (e)
                #    continue
                final_url = ResolveURL(resource_url)
                if (final_url.find("data:") == 0):
                    ###print ("Directly Imbedded URL: " + final_url)
                    continue
                resourceName = resource_url[resource_url.rfind("/") + 1:]
                try: 
                    #urllib.request.urlretrieve(final_url, resource_resolver.output_path)
                    ###print ("Before URL: " + resource_url + "(hostname=" + hostname + ")")
                    #print ("0=" + resource_url[0] + ", 1=" + resource_url[1], ", 2=" + resource_url[2] + ", 3=" + resource_url[3])
                    #print (str(resource_url[0] == '/') + ", " + str(resource_url[1] == '/'))

                    if (resource_url[0] == '/' and resource_url[1] == '/'):
                        resource_url = scheme + resource_url
                    elif (resource_url[0] == '/'):
                        resource_url = hostname + resource_url
                    elif (resource_url.find("://") < 0):
                        resource_url = hostname + "/" + resource_url
#                        resource_text = ResourceLoader.download(hostname + resource_url)
 #                   else:
                    ###print ("After URL: " + resource_url)
                    if (resource_url in pureURLs):
                        continue
                    pureURLs.append(resource_url)
                    #####resource_text = ResourceLoader.download(resource_url)
                    ###print ("Final_URL: " + resourceName + "   " + resource_url)
                    allURLs.append((level, resource_url, pageURL))
                    allResources.append(resourceName)
                    ###print ("Check: " + resource_url)
                    if resourceName.endswith(".css")  or  resourceName.endswith(".html"):
                        ###print ("Pushed: " + resource_url)
                        recursiveResourceList.append((level, resource_url))

                    count = count + 1 
                    #print ("Final URL: " + resource_url[resource_url.rfind("/") + 1:] + ", " + final_url + " (" + resource_url + ") downloaded at")
            
#                    print (resource_resolver.output_path)
#                    print()
                except Exception as e:
                    print ("FAILURE_Final_URL: " + final_url + "   " + resource_url)
                    print (e)
                    failedURLs.append((level, resource_url, pageURL))
                    failedResources.append(resourceName)
                    #print ("FAILURE: Final URL: " + final_url + " (" + resource_url + ") downloading at")
                    #print (resource_resolver.output_path)
                    #print(e) 
                    continue
                #resource_text = ResourceLoader.download(resource_resolver.resource_url)
                #resource_resolver.output_path.write_text(resource_text)




	     # Download all static URLs referenced in the stylesheets
        #css_link_tags = style_search.find_external_stylesheets(html_tree)
        #stylesheet_url_iter = (style_search.pick_href(it) for it in css_link_tags)

        #for resource_url in stylesheet_url_iter:
        #for resource_url in recursiveResourceList:
        elif pageURL.endswith(".css"):
            #print("CCS IN")
            #resource_resolver = deepcopy(markup_resolver)
            #resource_resolver.resource_url = resource_url
            # print ("RESOURCE_URL::: " + resource_url)
            #if resource_resolver.output_dir is None or resource_resolver.output_path is None:
            #    continue

            #resource_text = ResourceLoader.download(pageURL)
            #resource_text = ResourceLoader.download(resource_resolver.resource_url)

            #resource_resolver.output_dir.mkdir(parents=True, exist_ok=True)
            #resource_resolver.output_path.write_text(resource_text)

            (urlDictionary, rawUrlDictionary) = CCS_Find_Resources(contents)
        
            for resource in urlDictionary:
                resource = resource.strip()
                if (resource == "about:blank") or resource[0:5] == "data:" or len(resource) == 0:
                     continue
                #resource_resolver2 = deepcopy(markup_resolver)
                #resource_resolver2.resource_url = rawUrlDictionary[resource]

                #print ("Resource: " + resource + "(" + resource_resolver2.resource_url + ")")
                #response = requests.get(resource)
                #if resource_resolver2.output_dir is None or resource_resolver2.output_path is None:
                #    continue
                #resource_text2 = response.content #= ResourceLoader.download(resource_resolver2.resource_url)
                #try:
                #    resource_resolver2.output_dir.mkdir(parents=True, exist_ok=True)

                #except Exception as e:
                #    print (e)
                #    continue

                #urllib.request.urlretrieve("https://telegram.org/../img/dropdown_1x.png", resource_resolver2.output_path)
                try: 
                    #urllib.request.urlretrieve(resource, resource_resolver2.output_path)

                    if (rawUrlDictionary[resource][0] == '/' and rawUrlDictionary[resource][1] == '/'):
                         rawUrlDictionary[resource] = scheme + rawUrlDictionary[resource]
                    elif (rawUrlDictionary[resource][0] == '/'):
                        rawUrlDictionary[resource] = hostname + rawUrlDictionary[resource]
                    elif(rawUrlDictionary[resource].find("://") < 0):
                        rawUrlDictionary[resource] = hostname + "/" + rawUrlDictionary[resource]
#                        resource_text = ResourceLoader.download(hostname + resource_url)
 #                   else:
                    if (rawUrlDictionary[resource] in pureURLs):
                        continue
                    pureURLs.append(rawUrlDictionary[resource])
                    #####resource_text = ResourceLoader.download(rawUrlDictionary[resource])
                    #if (rawUrlDictionary[resource][0] == '/'):
                    #    resource_text = ResourceLoader.download(hostname + rawUrlDictionary[resource])

                    #else:
                    #    ResourceLoader.download(rawUrlDictionary[resource])
                    resourceName = rawUrlDictionary[resource][rawUrlDictionary[resource].rfind("/") + 1:] 
                    ###print ("Final_URL: " + resourceName + ", " + rawUrlDictionary[resource])
                    allURLs.append((level, rawUrlDictionary[resource], pageURL))
                    allResources.append(resourceName)

                    ###print ("Check: " + resource_url)
                    if resourceName.endswith(".css")  or  resourceName.endswith(".html"):
                        ###print ("Pushed: " + resource_url)
                        recursiveResourceList.append((level, resource_url))
                    #print ("Final_URL: " + rawUrlDictionary[resource][rawUrlDictionary[resource].rfind("/") + 1:] + ", " + resource + " (" + rawUrlDictionary[resource] + ") downloaded at")
                    #print (resource_resolver.output_path)
                    #print()
                    count = count + 1 
                except Exception as e:

                    ###print ("FAILURE: Final URL: " + resource + ", " + rawUrlDictionary[resource])
                    failedURLs.append((level, rawUrlDictionary[resource], pageURL))
                    failedResources.append(resource)
                    #print (resource_resolver.output_path)
                    #print (e)
                    continue
                #resource_resolver2.output_path.write_byte(resource_text2)
                #fileTemp = open("/home/skyer/temp.png", "wb") 
                #fileTemp.write(resource_text2)
                #fileTemp.close()
                #print(resource_resolver2.output_path)
                #return

        isFirst = False
        #print ("Level " + str(level) + " Static URLs: " + str(count - prevCount))
        #level = level + 1
        #levelCount.append(count - prevCount)
        #prevCount = count

    levelCount = [0] * (maxLevel + 1)

    index = 0
    for url in allURLs:
        index = index + 1
        levelCount[url[0]] = levelCount[url[0]] + 1

    print()

    print("<Static URLs>")
    index = 0
    for url in allURLs:
        print("Static_URL (Depth=" + str(url[0]) + "): " + str(allResources[index]) + "    " + str(url[1]) + " (Referer=" + str(url[2]) + ")")
        index = index + 1
    print()

    print("<Failed Static URLs>")
    index = 0
    for url in failedURLs:
        print("Failed_URL (level=" + str(url[0]) + "): " + str(failedResources[index]) + "    " + str(url[1]) + " (Referer=" + str(url[2]) + ")")
        index = index + 1

    if (len(failedURLs) == 0):
       print ("None")

    print()
    index = 0
    print("<Static URLs in Each Dependency Depth>")
    for eachCount in levelCount:
         print("[Depth " + str(index) + "] : " + str(eachCount))
         index = index + 1

    print()
    print("- Total Static URLs: " + str(len(allURLs)))
    print("- Total Failed URLs: " + str(len(failedURLs)))

if __name__ == '__main__':
    main(parse_args())


# EOF
