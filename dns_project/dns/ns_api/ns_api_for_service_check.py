from django.http                  import HttpResponse

def serviceCheck(request, *args, **kwargs):
        return HttpResponse('SERVICE_ALLIVE')
