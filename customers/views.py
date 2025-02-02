from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import InquiriesForm

# Create your views here.
def inquire(request):
    plan = request.GET.get('plan')
    if request.method == 'POST':
        form = InquiriesForm(request.POST)
        if form.is_valid():
            instance= form.save(commit=False)
            instance.plan=plan
            instance.save()
            messages.success(request, "Your request has been received you will receive your web analysis report within 24 hours ")
        return redirect('index')
    else:
        form = InquiriesForm()
        context = {
            'form': form,
            'plan': plan
        }
        return render(request, 'home/inquire.html', context)
