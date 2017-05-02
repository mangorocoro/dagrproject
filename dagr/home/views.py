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

        '''
        print("request.META = {}".format(request.META))
        for ele in request.META:
            print("{} = {}".format(ele, request.META[ele]))
        '''

        file = request.FILES['file']
        size = request.POST['size']
        print("file size is = {}".format(size))

        filename = str(file)
        fd = os.open(str(file), os.O_RDWR|os.O_CREAT)

        handle_uploaded_file(file, filename)

        # after file is uploaded get the data
        # this is currently giving me data on the copied file instance not the original file
        # need to find a way to get access to the original file on disk
        # find a way to know the directory name from where the file came from...
        lsresults = subprocess.check_output(["ls", "upload"]).decode("utf-8")
        print("lsresults = {}".format(lsresults))

        owner = subprocess.check_output(["stat", "-c", "'%U'", filename]).decode("utf-8")
        print("owner = {}".format(owner))

        byte_size = subprocess.check_output(["stat", "-c", "'%s'", filename]).decode("utf-8")
        print("size = {}".format(byte_size))




        last_access = subprocess.check_output(["stat", "-c", "'%x'", filename]).decode("utf-8")
        print("last_access = {}".format(last_access))

        last_data_modification = subprocess.check_output(["stat", "-c", "'%y'", filename]).decode("utf-8")
        print("last_data_modification = {}".format(last_data_modification))

        last_status_change = subprocess.check_output(["stat", "-c", "'%z'", filename]).decode("utf-8")
        print("last_status_change = {}".format(last_status_change))





        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")


def handle_uploaded_file(file, filename):

    localpath = subprocess.check_output(["realpath", filename]).decode("utf-8")
    print("localpath = {}".format(localpath))


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
    try:
        import pwd  # not available on all platforms
        userinfo = pwd.getpwuid(st[ST_UID])
    except (ImportError, KeyError):
        print("failed to get the owner name for", file)
    else:
        creator = userinfo[0]
        print("file owned by:", userinfo[0])

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

def metadataquery(request):
    if request == "POST":
        # get the search terms, None if nothing entered
        guid = str(request.FILES['guid'])
        path = str(request.FILES['path'])
        creationtime = str(request.FILES['creationtime'])
        modtime = str(request.FILES['modtime'])
        author = str(request.FILES['author'])
        size = str(request.FILES['size'])
        date = str(request.FILES['date'])
        name = str(request.FILES['name'])


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