import functools
from rx.subjects import Subject
import gc
 
class PayloadRequest(object):
    incoming_request = Subject()

    @classmethod
    def received_data(self, request):
        PayloadRequest.incoming_request.on_next(request[0])