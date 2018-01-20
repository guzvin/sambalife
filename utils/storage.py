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
        logger.debug(dir_name)
        logger.debug(file_name)
        dir_path_exists = os.path.exists(os.path.join(settings.MEDIA_ROOT, dir_name))
        logger.debug(dir_path_exists)
        if dir_path_exists:
            shutil.rmtree(os.path.join(settings.MEDIA_ROOT, dir_name))
        logger.debug(file_name)
        return name
