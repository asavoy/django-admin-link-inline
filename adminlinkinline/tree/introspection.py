"""
functionality for finding inverse foreign key relations in model classes
"""
from django.contrib.contenttypes.generic import ReverseGenericRelatedObjectsDescriptor
from django.db.models.base import ModelBase
from django.db.models.fields.related import ForeignRelatedObjectsDescriptor, SingleRelatedObjectDescriptor


INTROSPECTION_ERROR = """
%s

django_admin_link_inline caught an AttributeError while trying
to inspect %s looking for %s.
"""

def _get_members_of_type(obj, member_type):
    """
    Finds members of a certain type in obj.

    :param obj: A model instance or class.
    :param member_type: The type of the menber we are trying to find.
    :rtype: A :class:`list` of ``member_type`` found in ``obj``
    """
    
    if not issubclass(type(obj), ModelBase):
        obj = obj.__class__
        
    key_hash = []
    for key in dir(obj):
        try:
            attr = getattr(obj, key)
        except AttributeError as e:
            try:
                attr = obj.__dict__[key]
            except KeyError:
                raise AttributeError(INTROSPECTION_ERROR % (e, obj, member_type))

        if type(attr) is member_type:
            key_hash.append((key, attr))
    
    return key_hash

def get_foreign_key_desciptors(obj):
    """
    finds all :class:`~django.db.models.fields.ForeignRelatedObjectsDescriptor` in obj.
    
    :param obj: A model instance or class.
    """
    return _get_members_of_type(obj, ForeignRelatedObjectsDescriptor)