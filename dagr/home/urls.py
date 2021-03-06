# home/urls.py

from django.conf.urls import url
from home import views

urlpatterns = [
    url(r'^$', views.HomePageView.as_view(), name='home'),
    url(r'^about/$', views.AboutPageView.as_view(), name='about'),
    url(r'^bulkdataentry/$', views.BulkEntryPageView.as_view(), name='bulkdataentry'),
    url(r'^htmlparser/$', views.HtmlParserPageView.as_view(), name='htmlparser'),
    url(r'^metadataquery/$', views.metadataQueryPage, name='metadataquery'),
    url(r'^timerange/$', views.TimeRangePageView.as_view(), name='timerange'),
    url(r'^success/$', views.SuccessView.as_view(), name='success'),
    url(r'^upload/$', views.upload, name='upload'),
    url(r'^urlparser/$', views.urlParser, name='urlparser'),
    url(r'^metadataqueryresults/$', views.metadataqueryresults, name='metadataqueryresults'),
    url(r'^categorize/$', views.categorize, name='categorize'),
    url(r'^categorizeSubmission/$', views.categorizeSubmission, name='categorizeSubmission'),
    url(r'^bulk/$', views.bulk, name='bulk'),
    url(r'^insert/$', views.insert, name='insert'),
    url(r'^keywordSubmission/$', views.keywordSubmission, name='keywordSubmission'),
    url(r'^keywordPage/$', views.keywordPage, name='keywordPage'),
    url(r'^findorphans/$', views.findorphans, name='findorphans'),
    url(r'^queryresultspage/$', views.QueryResultsPage.as_view(), name='queryresultspage'),
    url(r'^timeRangeQueryResults/$', views.timeRangeQueryResults, name='timeRangeQueryResults'),
    url(r'^timerangedatavis/$', views.TimeRangeDataVis.as_view(), name='timerangedatavis'),
    url(r'^deleteChoice/$', views.deleteChoice, name='deleteChoice'),
    url(r'^delete/$', views.delete, name='delete'),
    url(r'^deleteSuccess/$', views.deleteSuccess.as_view(), name='deleteSuccess'),
    url(r'^reach/$', views.reach, name='reach'),
    url(r'^reachResults/$', views.reachResults, name='reachResults'),
    url(r'^categorizeDelete/$', views.categorizeDelete, name='categorizeDelete'),
    url(r'^modify/$', views.ModifyPageView, name='modify'),
    url(r'^modifySubmission/$', views.modifySubmission, name='modifySubmission'),
    url(r'^modified/$', views.modified, name='modified'),
    url(r'^editSuccess/$', views.editSuccess.as_view(), name='editSuccess'),
    url(r'^categorizeSuccess/$', views.categorizeSuccess.as_view(), name='categorizeSuccess'),
    url(r'^keywordSuccess/$', views.keywordSuccess.as_view(), name='keywordSuccess'),
]