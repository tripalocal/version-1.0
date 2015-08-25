import json
import traceback

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render_to_response


class AjaxProcessBase(object):
    http_method = None
    manipulation_function_prefix = None

    def _process_request_with_general_return(self, request, *args, **kwargs):
        try:
            # Get the class that need to be updated.
            cls = kwargs['model_class']
            request_dic = dict(getattr(request, self.http_method.upper()))

            # If it's process on one object.
            object_id = None
            object = None
            if 'object_id' in request_dic:
                object_id = request_dic['object_id']
                object = get_object_or_404(cls, id=object_id[0])
            elif 'object_id[]' in request_dic:
                object_id = request_dic['object_id[]']
                object = cls.objects.filter(id__in = object_id)

            operation = request_dic['operation'][0]

            manipulate_function_name = self.manipulation_function_prefix + operation
            manipulate_function = getattr(self, manipulate_function_name)
            extra_return = manipulate_function(request, object, **kwargs)
            base_result = {'success': True}
            if extra_return:
                base_result.update(extra_return)
            return HttpResponse(json.dumps(base_result), content_type='application/json')
        except:
            traceback.print_exc()
            return HttpResponse(json.dumps({'success': False}), content_type='application/json')

    def _generate_html(self, context, template):
        return render_to_response(template, context)

class AjaxDisptcherProcessorMixin(AjaxProcessBase):
    http_method = 'post'
    manipulation_function_prefix = '_manipulate_'


class AjaxGetProcessorMixin(AjaxProcessBase):
    http_method = 'get'
    manipulation_function_prefix = '_get_'

    def get(self, request, *args, **kwargs):
        if request.is_ajax():
            if request.GET['operation'] == 'index':
                context = super(AjaxGetProcessorMixin, self).get_context_data(request, *args, **kwargs)
                template = self.template
                return self._generate_html(context, template)
        else:
            return super(AjaxGetProcessorMixin, self).get(request, *args, **kwargs)

