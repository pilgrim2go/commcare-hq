from datetime import datetime, timedelta
import json
from django import template
from django.conf import settings
from django.utils.safestring import mark_safe


register = template.Library()

@register.filter
def JSON(obj):
    try:
        obj = obj.to_json()
    except AttributeError:
        pass
    return mark_safe(json.dumps(obj))

@register.filter
def dict_lookup(dict, key):
    '''Get an item from a dictionary.'''
    return dict.get(key)
    
@register.filter
def array_lookup(array, index):
    '''Get an item from an array.'''
    if index < len(array):
        return array[index]
    
@register.filter
def attribute_lookup(obj, attr):
    '''Get an attribute from an object.'''
    if (hasattr(obj, attr)):
        return getattr(obj, attr)
    

@register.simple_tag
def dict_as_query_string(dict, prefix=""):
    '''Convert a dictionary to a query string, minus the initial ?'''
    return "&".join(["%s%s=%s" % (prefix, key, value) for key, value in dict.items()])

@register.filter
def add_days(date, days=1):
    '''Return a date with some days added'''
    span = timedelta(days=days)
    try:
        return date + span
    except:
        return datetime.strptime(date,'%m/%d/%Y').date() + span 
    
@register.filter
def concat(str1, str2):
    """Concatenate two strings"""
    return "%s%s" % (str1, str2)

@register.simple_tag
def build_url(relative_path, request=None):
    """Attempt to build a URL from within a template"""
    return build_url_util(relative_path, request)

try:
    from resource_versions import resource_versions
except ImportError:
    resource_versions = {}
@register.simple_tag
def static(url):
    version = resource_versions.get(url)
    url = settings.STATIC_URL + url
    if version:
        url += "?version=%s" % version
    return url

@register.simple_tag
def get_report_analytics_tag(request):
    if 'reports' in request.path_info:
        report_name = request.path_info.split('reports/')[1][:-1].replace('_', ' ')
        return "_gaq.push(['_setCustomVar', 2, 'report', '%s', 3]);\n_gaq.push(['_trackEvent', 'Viewed Report', '%s']);" % (report_name, report_name)
    return ''