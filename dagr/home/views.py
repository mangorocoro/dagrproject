# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from .forms import DocumentForm
import os, time, sys
from stat import * # ST_SIZE etc
import MySQLdb
import uuid
from subprocess import call
import subprocess
import metadata_parser
from bs4 import BeautifulSoup
import urllib
import re



class HomePageView(TemplateView):
    '''
    def get(self, request, **kwargs):
        return render(request, 'index.html', context=None)
    '''
    template_name = 'index.html'

class AboutPageView(TemplateView):
    template_name = 'about.html'

class BulkEntryPageView(TemplateView):
    template_name = 'bulkentry.html'

class CategorizePageView(TemplateView):
    template_name = 'categorize.html'

class DeletePageView(TemplateView):
    template_name = 'delete.html'

class FindOrphansPageView(TemplateView):
    template_name = 'findorphans.html'

class HtmlParserPageView(TemplateView):
    template_name = 'htmlparser.html'

class InsertPageView(TemplateView):
    template_name = 'insert.html'

def upload(request):
    if request.method == 'POST':

        # extract file, filename, size, and local directory
        file = request.FILES['file']
        filename = str(file)
        size = request.POST['size']
        local_homedir = request.META['HOME']


        print("file = {}".format(file))
        print("filename = {}".format(filename))
        print("size = {}".format(size))
        print("local home directory = {}".format(local_homedir))



        # let's create a shell script on the local computer!
        # for preparation of local file metadata extraction
        createShellScript()


        # extract all relevant metadata from file
        extractLocalMetadata(filename, size, local_homedir)

        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")


def createShellScript():
    # if pathfinder script doesn't already exist, make it
    if not os.path.exists('pathfinder.sh'):
        with open('pathfinder.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('filename=$1\n')
            script.write('size-$2\n')
            script.write('homedir=$3\n')
            script.write('find $3 -type f -size $2 -name $filename 2>/dev/null\n')

    # if metadata extractor script doesn't already exist make it
    if not os.path.exists('metadataextractor.sh'):
        with open('metadataextractor.sh', 'w') as script:
            script.write('#!/bin/bash\n')
            script.write('filename=$1\n')
            script.write('''owner="$(stat -c '%U' ${filename})"''')
            script.write('''lastaccess="$(stat -c '%x' ${filename})"''')
            script.write('''lastmod="$(stat -c '%y' ${filename})"''')
            script.write('''laststatuschange="$(stat -c '%z' ${filename})"''')



def extractLocalMetadata(filename, size, local_homedir):

    filename_escaped = re.escape(filename)
    size_c = str(size) + "c"

    print("filename escaped = {}".format(filename_escaped))
    print("size_c = {}".format(size_c))

    # run script to get the paths
    proc = subprocess.Popen(["sh", "pathfinder.sh", filename_escaped, size_c, local_homedir], stdout=subprocess.PIPE)

    path_list = []
    # extract all the paths pathfinder returns you
    for row in proc.stdout:
        path_list.append(row.decode("utf-8").rstrip())
        print(row.decode("utf-8"))

    print("path_list = {}".format(path_list))

    # if there is more than one path in path list, choose the first one
    if len(path_list) != 1:
        localpath = path_list[0]
    elif len(path_list) == 0:
        raise Exception('Why is there no path?')
    else:
        localpath = path_list[0]

    print("local path extracted = {}".format(localpath))

    ##############################################
    # Still some issues with filenames with spaces
    ##############################################


    '''
    # start assigning metadata
    owner = subprocess.check_output(["stat", "-c", "'%U'", filename]).decode("utf-8")
    print("owner = {}".format(owner))

    last_access = subprocess.check_output(["stat", "-c", "'%x'", filename]).decode("utf-8")
    print("last_access = {}".format(last_access))

    last_data_modification = subprocess.check_output(["stat", "-c", "'%y'", filename]).decode("utf-8")
    print("last_data_modification = {}".format(last_data_modification))

    last_status_change = subprocess.check_output(["stat", "-c", "'%z'", filename]).decode("utf-8")
    print("last_status_change = {}".format(last_status_change))
    '''



def handle_uploaded_file(file, filename):


    try:
        st = os.stat(filename)
    except IOError:
        print("failed to get information about", file)
    else:
        size = ("{:.3f}".format(st[ST_SIZE] / 1024.0))
        print("file size: " + size + " KB")
        print("st[ST_MTIME] = {}".format(st[ST_MTIME]))
        date = st[ST_MTIME]
        modDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(date))
        date = st[ST_CTIME]
        creDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(date))
        print("file modified:", modDate)
        print("file created:", creDate)

    id = uuid.uuid4()


    if not os.path.exists('upload/'):
        os.mkdir('upload/')

    with open('upload/' + filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)





def urlParser(request):
    if request.method == "GET":
        url = request.GET.get('url')
        # if first 7 or 8 chars are not http:// or https:// append it
        http = "http://"
        https = "https://"
        if not url.startswith(http) or not url.startswith(https):
            url = http + url

        print("url = {}".format(url))
        page = metadata_parser.MetadataParser(url=url, search_head_only=False)
        print("page = {}".format(page.metadata))


        title = page.get_metadata('title')

        description = page.get_metadata('description')

        id = uuid.uuid4()

        date = page.get_metadata('pubdate')

        date = date[:10] + " " + date[11:len(date) - 1]

        last_modified = page.get_metadata('lastmod')

        last_modified = date[:10] + " " + date[11:len(date) - 1]

    return HttpResponseRedirect(reverse('success'))




def metadataqueryresults(request):
    print("AM I EVEN HERE?")
    if request.method == "POST":
        # get the search terms, None if nothing entered
        print("IM A POST LIKE IM SUPPOSED TO BE")
        print("request.POST = {}".format(request.POST))

        guid = str(request.POST.get('guid'))

        name = str(request.POST.get('name'))
        category = str(request.POST.get('category'))
        path = str(request.POST.get('path'))
        size = str(request.POST.get('size'))
        creationtime = str(request.POST.get('creationtime'))
        creator = str(request.POST.get('creator'))
        modtime = str(request.POST.get('modtime'))
        date = str(request.POST.get('date'))

        print("guid = {}".format(guid))
        print("name = {}".format(name))
        print("category = {}".format(category))
        print("path = {}".format(path))
        print("size = {}".format(size))
        print("creationtime = {}".format(creationtime))
        print("creator = {}".format(creator))
        print("modtime = {}".format(modtime))
        print("date = {}".format(date))



        return HttpResponseRedirect(reverse('success'))
    return HttpResponse("Failed")


class SuccessView(TemplateView):
    template_name = 'success.html'

class MetadataQueryPageView(TemplateView):
    template_name = 'metadataquery.html'


class ModifyPageView(TemplateView):
    template_name = 'modify.html'

class ReachPageView(TemplateView):
    template_name = 'reach.html'

class TimeRangePageView(TemplateView):
    template_name = 'timerange.html'