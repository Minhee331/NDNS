from django.shortcuts import render
from searchEngine.settings import *

# Create your views here.
def index(request):
    return render(request, "index.html", {'STATIC_URL': STATIC_URL})


def search(request, searchVal):
    # searchVal : 검색어
    
    return render(request, "search.html", {'STATIC_URL': STATIC_URL, 'searchVal':searchVal})

