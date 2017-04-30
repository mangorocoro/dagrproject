# home/views.py
from django.shortcuts import render
from django.views.generic import TemplateView
from django.http import HttpResponseRedirect, HttpResponse
from django.core.urlresolvers import reverse, reverse_lazy
from .forms import DocumentForm
import os, time
from stat import * # ST_SIZE etc
import MySQLdb
import uuid
from django.views.generic.edit import FormView


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
        handle_uploaded_file(request.FILES['file'], str(request.FILES['file']))
        return HttpResponseRedirect(reverse('success'))

    return HttpResponse("Failed")


def handle_uploaded_file(file, filename):
    print("file is {} and filename is {}".format(file, filename))
    '''
    conn = MySQLdb.connect(host="localhost",
                           user="root",
                           passwd="p",
                           db="Documents")
    x = conn.cursor()
    '''
    #file = "/home/ryan/Desktop/docParser.py"
    #temp = file.split("/")
    #title = temp[len(temp) - 1]
    #print title
    #print "file storage path:", file

    print "file = {}".format(file.file)

    print("os.fstat(file) = {}".format(os.stat(file)))
    print("os.fstat(file.name) = {}".format(os.stat(file.name)))

    try:
        st = os.stat(file.name)
    except IOError:
        print("failed to get information about", file)
    else:
        size = ("{:.3f}".format(st[ST_SIZE] / 1024.0))
        print
        "file size: " + size + " KB"
        print
        st[ST_MTIME]
        date = st[ST_MTIME]
        modDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(date))
        date = st[ST_CTIME]
        creDate = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(date))
        print
        "file modified:", modDate
        print
        "file created:", creDate
    try:
        import pwd  # not available on all platforms
        userinfo = pwd.getpwuid(st[ST_UID])
    except (ImportError, KeyError):
        print
        "failed to get the owner name for", file
    else:
        creator = userinfo[0]
        print
        "file owned by:", userinfo[0]

    id = uuid.uuid4()

    '''
    x.execute(""" INSERT INTO DAGR VALUES (%s, %s, %s, %s, %s, %s, %s) """,
              (str(id), title, file, size, creDate, creator, ' '))
    conn.commit()
    x.execute("""SELECT * FROM DAGR""")
    for row in x:
        print(row)
    conn.close()
    '''

    if not os.path.exists('upload/'):
        os.mkdir('upload/')

    with open('upload/' + filename, 'wb+') as destination:
        for chunk in file.chunks():
            destination.write(chunk)

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