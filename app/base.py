import json
import traceback

from django.shortcuts import get_object_or_404
from django.http import HttpResponse

class AjaxProcessBase(object):
    http_method = None
    manipulation_function_prefix = None

    def _process_request_with_general_return(self, request, *args, **kwargs):
        try:
            cls = kwargs['model_class']
            request_dic = getattr(request, self.http_method.upper())
            object_id = request_dic['object_id']
            operation = request_dic['operation']
            object = get_object_or_404(cls, id=object_id)
            manipulate_function_name = self.manipulation_function_prefix + operation
            manipulate_function = getattr(self, manipulate_function_name)
            extra_return = manipulate_function(request, object)
            base_result = {'success': True}
            if extra_return:
                base_result.update(extra_return)
            return HttpResponse(json.dumps(base_result), content_type='application/json')
        except:
            traceback.print_exc()
            return HttpResponse(json.dumps({'success': False}), content_type='application/json')

class AjaxDisptcherProcessorMixin(AjaxProcessBase):
    http_method = 'post'
    manipulation_function_prefix = '_manipulate_'


class AjaxGetProcessorMixin(AjaxProcessBase):
    http_method = 'post'
    manipulation_function_prefix = '_get_'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            self._process_request_with_general_return()
        else:
            return super(AjaxGetProcessorMixin, self).get(request, *args, **kwargs)
