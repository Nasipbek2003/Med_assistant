from django.shortcuts import render

def home_view(request):
    return render(request, 'main.html')

def about_view(request):
    return render(request, 'about.html')

def chat_view(request):
    return render(request, 'chat.html')

def info_view(request):
    return render(request, 'info.html')

def clinics_map(request):
    return render(request, 'clinics_map.html') 