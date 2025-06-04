from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from recipes.views import short_link_redirect

urlpatterns = [

    path('api/', include('users.urls')),
    path('api/', include('recipes.urls')),
    path("api/s/<int:pk>/", short_link_redirect, name="short-link"),
    path("admin/", admin.site.urls),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
