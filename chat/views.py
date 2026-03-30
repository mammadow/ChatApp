from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from chat.models import ChatMessage


def registerPage(request, *args, **kwargs):
	if request.user.is_authenticated:
		return redirect("chat-page")

	form = UserCreationForm(request.POST or None)
	if request.method == "POST" and form.is_valid():
		user = form.save()
		login(request, user)
		return redirect("chat-page")

	return render(request, "chat/RegisterPage.html", {"form": form})


@login_required(login_url="login-user")
def chatPage(request, *args, **kwargs):
	recent_messages = list(
		ChatMessage.objects.select_related("user").order_by("-created_at")[:50]
	)
	context = {
		"messages": list(reversed(recent_messages)),
	}
	return render(request, "chat/chatPage.html", context)
