from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from recipes.views import short_link_redirect


urlpatterns = [

    path('api/', include('api.urls')),
    path("admin/", admin.site.urls),
    path("s/<int:pk>/", short_link_redirect, name="short-link"),

]

if settings.DEBUG:
    urlpatterns += \
        static(settings.STATIC_URL, document_root=settings.STATIC_URL)
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
