import os
import sys

# add backend dir to python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "payEase.settings")
# Force production mode
os.environ["DEBUG"] = "False"
os.environ["ALLOWED_HOSTS"] = "*"

import django
django.setup()

from django.test import Client
import traceback

c = Client()

try:
    response = c.get('/tenant/')
    print("Status Code:", response.status_code)
    if response.status_code == 500:
        print("It returned a 500, but test client might suppress traceback if handled by template. Let's see if we can trigger it directly.")
except Exception as e:
    print("Exception caught!")
    traceback.print_exc()
