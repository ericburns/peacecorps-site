import logging

from django.conf import settings
from django.contrib.auth import backends
from django.utils.functional import empty, LazyObject
from django.utils.module_loading import import_string

from .models import Editor


class EditorBackend(backends.ModelBackend):
    """Always return an Editor rather than a generic User"""

    def get_user(self, user_id):
        try:
            return Editor.objects.get(pk=user_id)
        except Editor.DoesNotExist:
            return None


class LoggingStorage(LazyObject):
    """Implements the Storage API, but proxies all calls through after logging
    relevant data. The underlying storage must be configured or an exception
    is thrown."""
    def _setup(self):
        self._wrapped = import_string(settings.LOGGED_FILE_STORAGE)()
        self.logger = logging.getLogger('peacecorps.files')

    @property
    def wrapped(self):
        if self._wrapped is empty:
            self._setup()
        return self._wrapped

    def save(self, name, content):
        """Pass through, then log."""
        clean_name = self.wrapped.save(name, content)
        self.logger.info("Saved file %s", clean_name)
        return clean_name

    def delete(self, name):
        """Pass through, then log."""
        result = self.wrapped.delete(name)
        self.logger.info("Deleted file %s", name)
        return result