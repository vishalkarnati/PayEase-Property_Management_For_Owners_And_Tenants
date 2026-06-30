import os
import sys

# Add the 'backend' directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payEase.settings")

from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()

# Vercel serverless functions look for 'app' by default in Python projects
app = application
