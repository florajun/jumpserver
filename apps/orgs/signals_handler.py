# -*- coding: utf-8 -*-
#

from django.db.models.signals import m2m_changed
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import Organization, OrganizationMember
from .hands import set_current_org, current_org, Node, get_current_org
from perms.models import AssetPermission
from users.models import UserGroup


@receiver(post_save, sender=Organization)
def on_org_create_or_update(sender, instance=None, created=False, **kwargs):
    if instance:
        old_org = get_current_org()
        set_current_org(instance)
        node_root = Node.org_root()
        if node_root.value != instance.name:
            node_root.value = instance.name
            node_root.save()
        set_current_org(old_org)

    if instance and not created:
        instance.expire_cache()


def _remove_users(model, user, org, reverse=False):
    m2m_model = model.users.through
    if reverse:
        m2m_field_name = model.users.field.m2m_reverse_field_name()
    else:
        m2m_field_name = model.users.field.m2m_field_name()
    m2m_model.objects.filter(**{'user': user, f'{m2m_field_name}__org_id': org.id}).delete()


@receiver(post_delete, sender=OrganizationMember)
def on_org_user_deleted(signal, sender, instance, **kwargs):
    old_org = current_org
    org = instance.org
    user = instance.user
    set_current_org(org)
    _remove_users(AssetPermission, user, org)
    _remove_users(UserGroup, user, org, reverse=True)
    set_current_org(old_org)


@receiver(m2m_changed, sender=Organization.members.through)
def on_org_user_changed(sender, instance=None, **kwargs):
    if isinstance(instance, Organization):
        old_org = current_org
        set_current_org(instance)
        if kwargs['action'] == 'pre_remove':
            users = kwargs['model'].objects.filter(pk__in=kwargs['pk_set'])
            for user in users:
                perms = AssetPermission.objects.filter(users=user)
                user_groups = UserGroup.objects.filter(users=user)
                for perm in perms:
                    perm.users.remove(user)
                for user_group in user_groups:
                    user_group.users.remove(user)
        set_current_org(old_org)
#
#
# @receiver(m2m_changed, sender=Organization.admins.through)
# def on_org_admin_change(sender, **kwargs):
#     Organization._user_admin_orgs = None
