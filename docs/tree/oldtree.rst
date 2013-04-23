.. _oldtree_explanation:

Admin support for model trees with more than 2 levels of related items (deprecated)
===================================================================================

The single most annoying problem you will encounter when building django apps,
is that after you discovered the niceties of 
:attr:`~django.contrib.admin.ModelAdmin.inlines`, you find out that only
1 level of :attr:`~django.contrib.admin.ModelAdmin.inlines`
is supported. It does not support any form of recursion.

AdminLinkInline can not make recursive either, because that would become
a mess. What is *can* do, is display links to all related models. This way you have
them in reach where you need them. There is no need to go back to the admin and
select a different section to edit the related models.

.. image:: related.png

In the above picture, at the bottom of the ``Bars`` fieldset, there is a small
*+* button [#f1]_. Using this button you can create new ``Bar`` objects which have a
relation to the current ``Foo`` object. Just like with foreign key fields, the
*+* button [#f1]_ opens a popup in which you can create a new related item. 

The items above the *+* button [#f1]_ are all ``Bar`` objects that have a foreign key
which points to the current ``Foo`` object. Clicking them will let you edit them.

Implementing the tree
---------------------

To implement the tree first of all, you have to ensure that ``adminlinkinline`` comes
before ``django.contrib.admin`` in the ``INSTALLED_APPS`` section of your settings
file. This is because adminlinkinline needs to override the `admin/index.html` template.
Since the related items that point to ``Foo`` can now be accessed from the ``foo``
change_view, it is nolonger needed that ``Bar`` is displayed in editable models list
of the ``Foobar`` app. Just like
`InlineModelAdmin <http://docs.djangoproject.com/en/dev/ref/contrib/admin/#inlinemodeladmin-objects>`_ 
we want the 'inlined'
models to be excluded from the app list.

.. image:: invisible.png

This is how we want the ``Foobar`` app listing to look, with ``Foo`` visible and
``Bar`` excluded from the listing. In fact, that is what you can do with the
:class:`~django.contrib.admin.ModelAdmin` classes inside :mod:`adminlinkinline.tree.admin.relation`, as long as
you make sure that the `admin/index.html` template is read from the :mod:`adminlinkinline`
templates folder.

This is how the admin is defined to get the screenshots::

    from django.contrib import admin
    from adminlinkinline.tree.admin.relation import *

    from foobar.models import Foo, Bar

    @L10n
    class FooAdmin(ForeignKeyAwareModelAdmin):
        """Admin class for the Foo model"""
        model = Foo

        fieldsets = (
            (None, {
                'fields': ('bar', 'barstool')
            }),
            ('An thingy', {
                'fields': ('website', 'city', 'address')
            }),
        )

    class BarAdmin(InvisibleModelAdmin):
        model = Bar
        parent_link = 'foo'

    admin.site.register(Foo, FooAdmin)
    admin.site.register(Bar, BarAdmin)

As you can see the ``ModelAdmin`` classes used are 
:class:`~adminlinkinline.tree.admin.relation.InvisibleModelAdmin` and
:class:`~adminlinkinline.tree.admin.relation.ForeignKeyAwareModelAdmin`.

:class:`~adminlinkinline.tree.admin.relation.ForeignKeyAwareModelAdmin` is aware
of the models that have a ``ForeignKey`` pointing to the model which it
makes editable. 

In this case, ``FooAdmin`` makes ``Foo`` editable, and ``Bar`` has a 
``ForeignKey`` which points to ``Foo``. ``FooAdmin`` is fully aware of
this! In fact it will make you aware as well, because it will display
all the related ``Bar`` models in ``Foo``'s :func:`~django.contrib.admin.ModelAdmin.change_view`.

As said we'd like to have ``Bar`` be invisible in the ``Foobar`` app listing.
That is where :class:`~adminlinkinline.tree.admin.relation.InvisibleModelAdmin`
comes into play. Using :class:`~adminlinkinline.tree.admin.relation.InvisibleModelAdmin`
instead of a normal :class:`~django.contrib.admin.ModelAdmin` will hide the model from the app listing.

You could even use a :class:`~adminlinkinline.tree.admin.relation.ForeignKeyAwareModelAdmin`
in place of the :class:`~adminlinkinline.tree.admin.relation.InvisibleModelAdmin`
because it can be made invisible as well. Using these 2 :class:`~django.contrib.admin.ModelAdmin` classes,
mixed with regular
`InlineModelAdmin <http://docs.djangoproject.com/en/dev/ref/contrib/admin/#inlinemodeladmin-objects>`_
you can create deep trees and manage them
too.

----

.. [#f1] The '+' button and the fieldset for all the related items will only
    show up **AFTER** you save the model. This is because you can't create
    relations to objects that do not yet exist.