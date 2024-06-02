from __future__ import absolute_import
from  django.conf import settings
import os

from celery import Celery
from celery.schedules import crontab
from django.conf import settings
from datetime import timedelta

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'api.settings')

app = Celery('api')
app.conf.enable_utc= False
app.conf.update(timezone='Asia/Kolkata')
app.config_from_object(settings, namespace='CELERY')
app.autodiscover_tasks()


app.conf.beat_schedule = {
'get_joke_3s': {
'task': 'print_msg_main',
'schedule': crontab(minute="*/3"),
},
'get_joke_3s_x': {
'task': 'print_msg_main_x',
'schedule': crontab(minute="*/3"),
},
'get_joke_1h': {
'task': 'log_sheet',
'schedule': crontab(hour="*/2", minute=0),
},
'get_joke_2h': {
'task': 'update_price',
'schedule': crontab(hour="*/2", minute=0),
}
}
@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))

#crontab(minute="*/2"),
# hour="*", minute=0