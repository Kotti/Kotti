"""Monkey patches weeEe!
"""

import urllib
from webob.request import BaseRequest

PATH_SAFE = '/:@&+$,'

class BaseRequestPatches(object): # pragma: no cover
    """See https://bitbucket.org/dnouri/webob/changeset/bb042d67bca1
    """
    @property
    def application_url(self):
        return self.host_url + urllib.quote(
            self.environ.get('SCRIPT_NAME', ''), PATH_SAFE)

    @property
    def path_url(self):
        return self.application_url + urllib.quote(
            self.environ.get('PATH_INFO', ''), PATH_SAFE)

    @property
    def path(self):
        return (urllib.quote(self.script_name, PATH_SAFE) +
                urllib.quote(self.path_info, PATH_SAFE))

BaseRequest.application_url = BaseRequestPatches.application_url
BaseRequest.path_url = BaseRequestPatches.path_url
BaseRequest.path = BaseRequestPatches.path
