# home/urls.py

from django.conf.urls import url
from home import views

urlpatterns = [
    url(r'^$', views.HomePageView.as_view(), name='home'),
    url(r'^about/$', views.AboutPageView.as_view(), name='about'),
    url(r'^bulkdataentry/$', views.BulkEntryPageView.as_view(), name='bulkdataentry'),
    url(r'^categorize/$', views.CategorizePageView.as_view(), name='categorize'),
    url(r'^delete/$', views.DeletePageView.as_view(), name='delete'),
    url(r'^findorphans/$', views.FindOrphansPageView.as_view(), name='findorphans'),
    url(r'^htmlparser/$', views.HtmlParserPageView.as_view(), name='htmlparser'),
    url(r'^insert/$', views.InsertPageView.as_view(), name='insert'),
    url(r'^metadataquery/$', views.MetadataQueryPageView.as_view(), name='metadataquery'),
    url(r'^modify/$', views.ModifyPageView.as_view(), name='modify'),
    url(r'^reach/$', views.ReachPageView.as_view(), name='reach'),
    url(r'^timerange/$', views.TimeRangePageView.as_view(), name='timerange'),
    url(r'^success/$', views.SuccessView.as_view(), name='success'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^urlparser/$', views.urlParser, name='urlparser'),
    url(r'^metadataqueryresults/$', views.metadataqueryresults, name='metadataqueryresults'),
]