from django import template
from django.template.defaultfilters import stringfilter
from datetime import datetime
import re

register = template.Library()

@register.filter(name='currency')
def currency(value):
    """Format a number as currency (Rs. 1,234,567)"""
    try:
        value = float(value)
        return f"Rs. {value:,.2f}".replace(".00", "")
    except (ValueError, TypeError):
        return value

@register.filter(name='status_badge')
def status_badge(status):
    """Return appropriate CSS classes for status badges"""
    status_lower = str(status).lower()
    
    if status_lower in ['paid', 'approved', 'active', 'completed']:
        return "bg-emerald-100 text-emerald-700 border-emerald-200"
    elif status_lower in ['pending', 'processing', 'in progress']:
        return "bg-amber-100 text-amber-700 border-amber-200"
    elif status_lower in ['rejected', 'cancelled', 'failed', 'inactive']:
        return "bg-red-100 text-red-700 border-red-200"
    elif status_lower in ['draft', 'new']:
        return "bg-slate-100 text-slate-700 border-slate-200"
    else:
        return "bg-blue-100 text-blue-700 border-blue-200"

@register.filter(name='percentage')
def percentage(value, total):
    """Calculate percentage"""
    try:
        value = float(value)
        total = float(total)
        if total == 0:
            return 0
        return int((value / total) * 100)
    except (ValueError, TypeError):
        return 0

@register.simple_tag(takes_context=True)
def has_role(context, *roles):
    """Check if current user has any of the given roles"""
    request = context.get('request')
    if not request or not request.user.is_authenticated:
        return False
        
    if request.user.is_superuser:
        return True
        
    # Implement actual role checking logic here based on your user model
    # For now, placeholder returning True if superuser
    return False

@register.simple_tag(takes_context=True)
def is_active_nav(context, nav_name):
    """Return active CSS classes if nav_name matches context active_nav"""
    active_nav = context.get('active_nav', '')
    if active_nav == nav_name:
        return 'bg-blue-600/20 text-blue-400'
    return 'text-slate-400 hover:bg-slate-800 hover:text-white'

@register.filter(name='format_date')
def format_date(value):
    """Format date nicely"""
    if not value:
        return ""
    try:
        if isinstance(value, str):
            # Try to parse if it's a string, mostly simple handling
            pass
        return value.strftime("%d %b, %Y")
    except AttributeError:
        return value

@register.inclusion_tag('welfare_app/components/pagination.html')
def show_pagination(page_obj):
    """Render pagination component"""
    return {'page_obj': page_obj}
