from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('family.urls')),
]

# Timeweb WSGI не раздаёт static сам — всегда через Django
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
# исходники из STATICFILES_DIRS (scss/css, js), если collectstatic ещё не отработал
urlpatterns += staticfiles_urlpatterns()
