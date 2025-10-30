from django.shortcuts import render

# Create your views here.
def home(request):
    lang = request.GET.get('lang', 'bn')
    context = {
        'lang': lang
    }
    return render(request, 'home.html', context)


def signup(request):
    
    return render(request, 'registration_template.html', )