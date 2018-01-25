from django.urls import reverse
from django.http import HttpResponseRedirect, HttpResponseBadRequest
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model
import ast
import inspect
import json
import logging

logger = logging.getLogger('django')


class TermsAndConditionsMiddleware(MiddlewareMixin):

    ignored_funcs = ['accept_terms_conditions']
    login_required_decorator = 'login_required'

    def process_view(self, request, view_func, view_args, view_kwargs):
        logger.debug('######## TERMS AND CONDITIONS TERMS AND CONDITIONS TERMS AND CONDITIONS ##########')
        logger.debug(request.path)
        logger.debug(reverse('terms'))
        logger.debug(request.path.startswith(reverse('terms')))
        if request.method != 'GET' and view_func.__name__ not in self.ignored_funcs and \
           not request.path.startswith(reverse('admin:index')) and \
           self.login_required_decorator in get_decorators(view_func):
            user_model = get_user_model()
            try:
                current_user = user_model.objects.get(pk=request.user.id)
                if current_user.terms_conditions is False:
                    if 'output' in view_kwargs and view_kwargs.get('output') == 'json':
                        return HttpResponseBadRequest(json.dumps({'terms_and_conditions': True}),
                                                      content_type='application/json')
                    return HttpResponseRedirect(request.META.get('HTTP_REFERER', reverse('store')))
            except user_model.DoesNotExist as e:
                logger.error(e)
                return HttpResponseBadRequest()


def get_decorators(cls):
    target = cls
    decorators = []

    def visit_function_def(node):
        for n in node.decorator_list:
            name = ''
            if isinstance(n, ast.Call):
                name = n.func.attr if isinstance(n.func, ast.Attribute) else n.func.id
            else:
                name = n.attr if isinstance(n, ast.Attribute) else n.id

            decorators.append(name)

    node_iter = ast.NodeVisitor()
    node_iter.visit_FunctionDef = visit_function_def
    node_iter.visit(ast.parse(inspect.getsource(target)))
    return decorators
