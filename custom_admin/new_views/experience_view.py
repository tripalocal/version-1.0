__author__ = 'lyy'
from django.views.generic.edit import FormMixin
from django.views.generic import ListView
from django.utils.decorators import method_decorator

from app.base import AjaxDisptcherProcessorMixin
from app.decorators import ajax_form_validate
from experiences.models import Experience
from custom_admin.forms import ExperienceUploadForm

class ExperienceView(AjaxDisptcherProcessorMixin, FormMixin, ListView):
    model = Experience
    template_name = 'custom_admin/experiences.html'
    context_object_name = 'experience_list'

    def get_context_data(self, **kwargs):
        context = super(ExperienceView, self).get_context_data(**kwargs)
        experinece_list = Experience.objects.all()
        for exp in experinece_list:
            exp.get_experience_i18n_info()
        context['experience_list'] = experinece_list
        return context

    @method_decorator(ajax_form_validate(form_class=ExperienceUploadForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=Experience)

    def _manipulate_post_status(self, request, experience):
        experience.status = request.POST['status']
        experience.save()