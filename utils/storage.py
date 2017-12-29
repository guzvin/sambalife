from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import shutil
import logging

logger = logging.getLogger('django')


class OverWriteStorage(FileSystemStorage):
    def get_available_name(self, name, max_length=None):
        logger.debug('@@@@@@@@@@ STORAGE @@@@@@@@@@@@@')
        dir_name, file_name = os.path.split(name)
        shutil.rmtree(os.path.join(settings.MEDIA_ROOT, dir_name))
        return name
