from django.contrib import admin
from django.http import HttpResponseRedirect
from django.forms.models import modelformset_factory
from django.core import urlresolvers
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy as _

from adminlinkinline.tree.introspection import get_foreign_key_desciptors
from adminlinkinline.tree.admin.formsets import VisiblePrimaryKeyFormset


class ForeignKeyAwareModelAdmin(admin.ModelAdmin):
    """
    An admin class that display links to related items.
    
    This can be used for hierarchies of object deeper then 3
    levels, where :class:`InlineModelAdmin` can not be used anymore, but
    the parent/child relation is still there.
    
    usage::
    
        from django_admin_link_inline.tree.admin.relation import ForeignKeyAwareModelAdmin
        
        class SomeAdmin(ForeignKeyAwareModelAdmin):
            children = [SomeModelThatPointsToUs, AnotherModelThatPointsTous]

        admin.site.register(SomeModelWithLotsOfRelations, SomeAdmin)
    
    This will add the ``SomeModelThatPointsToUs`` and
    ``AnotherModelThatPointsTous`` to the ``SomeModelWithLotsOfRelations``
    admin interface and you can add these children or edit them there.
    
    See :class:`InvisibleModelAdmin` if you want to hide the admin interface
    for ``SomeModelThatPointsToUs`` and ``AnotherModelThatPointsTous``
    admin interface from the admin listing.
    
    .. attribute:: auto_aware
    
        If ``auto_aware`` is true, the admin will find out for itself which
        models are child nodes, by inspecting it's managers.
        
    .. attribute:: parent_link
        
        To have sane breadcrumbs if the :class:`~django_admin_link_inline.tree.admin.relation.ForeignKeyAwareModelAdmin`
        is used as child of another :class:`~django_admin_link_inline.tree.admin.relation.ForeignKeyAwareModelAdmin`
        and make the save button return to the parent instead of the app listing, the
        ``parent_link`` should be set.
        
        It must be set to the *name* of the ``ForeignKey`` that points to the
        parent.
    
    .. attribute:: children
        
        If the order of the children should be changed or not all children
        should be displayed, you can specify the children manually.
        
        children should be set to a list of models that are child nodes of the
        model class that this admin class makes editable:

    """
    change_form_template = 'tree/admin/change_form_with_related_links.html'
    
    auto_aware = True
    _children = None
    
    _real_descriptor_cache = None

    @property
    def _descriptor_cache(self):
        if self._real_descriptor_cache is None:
            self._real_descriptor_cache = dict(
                [(x[1].related.model, x[0])
                 for x in get_foreign_key_desciptors(self.model)]
            )
        return self._real_descriptor_cache 

    @property
    def children(self):
        if self._children is None:
            if self.auto_aware:
                self.children = self._descriptor_cache.keys()
            else:
                self.children = []
        return self._children

    @children.setter
    def children(self, value):
        self._children = value

    class Media:
        js = (
            'adminlinkinline/js/adminoverride.js',
        )

    def change_view(self, request, object_id, form_url='', extra_context=None):
        inline_links = {}
        inline_links['extra_forms'] = self.extra_forms(object_id)

        if extra_context:
            inline_links.update(extra_context)
            
        return super(ForeignKeyAwareModelAdmin, self).change_view(
            request, object_id, form_url, inline_links
        )

    def extra_forms(self, object_id):

        instance = self.model.objects.get(pk=object_id)
                
        extra_formsets = []

        for child in self.children:
            factory = modelformset_factory(child,
                                           extra=0,
                                           fields=['id'],
                                           formset=VisiblePrimaryKeyFormset)
            descriptor_name = self._descriptor_cache[child]
            descriptor = getattr(instance, descriptor_name)
            
            # create formset
            form = factory(queryset=descriptor.all())

            # this will find the name of the property in the model
            # the descriptor's inverse references
            try:
                field_name = descriptor.core_filters.keys().pop().split('__')[0]
            except Exception:
                field_name = instance._meta.object_name.lower()
            
            # find url for the + button
            url_descriptor = (self.admin_site.name,
                              child._meta.app_label,
                              child._meta.object_name.lower())
            url_pattern = '%s:%s_%s_add' % url_descriptor
            url = urlresolvers.reverse(url_pattern)
                
            #add properties to the formset            
            form.parent = instance            
            form.name = child.__name__.lower()
            form.title = child._meta.verbose_name_plural
            form.addurl = "%s?%s=%s" % (url, field_name, object_id)
            
            extra_formsets.append(form)

        return extra_formsets


class InvisibleModelMixin(admin.ModelAdmin):
    def get_model_perms(self, request):
        """
        Return empty perms dict thus hiding the model from admin index.
        http://stackoverflow.com/a/4871511
        """
        return {}


class InvisibleModelAdmin(InvisibleModelMixin):
    """
    An admin class that can be used as admin for children
    of :class:`~adminlinkinline.tree.admin.relation.ForeignKeyAwareModelAdmin`.
    
    This way they will be hidden in the admin interface
    so they can only be accessed via ``ForeignKeyAwareModelAdmin``.
    usage::
        
        from django.db import models
        from django.contrib import admin
        from adminlinkinline.tree.admin.relation import *
        
        class Bar(models.Model):
            foo = models.ForeignKey(Foo, related_name='bars')
            label = models.CharField(max_length=255)
            
        class BarAdmin(InvisibleModelAdmin):
            model = Bar
            parent_link = 'foo'
    
        admin.site.register(Bar, BarAdmin)
        
    .. attribute:: parent_link
        
        When :class:`~adminlinkinline.tree.admin.relation.InvisibleModelAdmin`
        is used, it is no longer displayed in the admin listing as an editable
        model. To have sane breadcrumbs and make the save button return to the
        parent instead of the app listing, the ``parent_link`` should be set.
        
        It must be set to the *name* of the ``ForeignKey`` that points to the
        parent.
    """
    # TODO: Consider overriding ModelAdmin.add_view()
    # ...   to fix the "Save and add another" button

    # TODO: Delete on a child model should redirect to the parent model

    change_form_template = 'tree/admin/change_form_with_parent_link.html'

    def change_view(self, request, object_id, form_url='', extra_context=None):

        # retrieve link to parent for breadcrumb path
        defaults = self._get_parent_link(self.model.objects.get(pk=object_id))

        if extra_context:
            defaults.update(extra_context)

        return super(InvisibleModelAdmin, self).change_view(
            request, object_id, form_url, defaults
        )

    def response_change(self, request, obj):
        """
        If (and only if) user clicked 'Save', redirect to parent model
        """
        opts = obj._meta
        verbose_name = opts.verbose_name
        parent_msg = _("You've been redirected to the parent object.")
        lookups = {
            'name': force_unicode(verbose_name), 'obj': force_unicode(obj)
        }
        if '_save' in request.POST:
            msg = parent_msg + ' ' + _(
                'The %(name)s "%(obj)s" was changed successfully.') % lookups
            self.message_user(request, msg)
            parent = self._get_parent_link(obj)
            return HttpResponseRedirect(parent.get('parent_model_url', '../'))

        return super(InvisibleModelAdmin, self).response_change(request, obj)

    def _get_parent_link(self, obj=None):
        parent_link_data = {}
        if hasattr(self, 'parent_link'):
            parent_link = getattr(self.model, self.parent_link)

            parent = parent_link.__get__(obj)
            parent_type_name = parent._meta.object_name.lower()
            parent_id = str(parent_link.field.value_from_object(obj))

            info = (self.admin_site.name,
                    parent._meta.app_label,
                    parent_type_name)

            parent_link_data['parent_model_url'] = urlresolvers.reverse(
                "%s:%s_%s_change" % info,
                args=[parent_id]
            )
            parent_link_data['parent_name'] = "%s %s" % (
                force_unicode(parent._meta.verbose_name),
                parent
            )

        return parent_link_data
