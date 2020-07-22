import uuid

from django.db import models
from django.utils.translation import ugettext_lazy as _

from common.utils import is_uuid
from common.const.choices import ROLE


class Organization(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    name = models.CharField(max_length=128, unique=True, verbose_name=_("Name"))
    created_by = models.CharField(max_length=32, null=True, blank=True, verbose_name=_('Created by'))
    date_created = models.DateTimeField(auto_now_add=True, null=True, blank=True, verbose_name=_('Date created'))
    comment = models.TextField(max_length=128, default='', blank=True, verbose_name=_('Comment'))
    members = models.ManyToManyField('users.User', related_name='orgs', through='orgs.OrganizationMember',
                                     through_fields=('org', 'user'))

    orgs = None
    CACHE_PREFIX = 'JMS_ORG_{}'
    ROOT_ID = '00000000-0000-0000-0000-000000000000'
    ROOT_NAME = 'ROOT'
    DEFAULT_ID = 'DEFAULT'
    DEFAULT_NAME = 'DEFAULT'
    SYSTEM_ID = '00000000-0000-0000-0000-000000000002'
    SYSTEM_NAME = 'SYSTEM'
    _user_admin_orgs = None

    class Meta:
        verbose_name = _("Organization")

    def __str__(self):
        return self.name

    def set_to_cache(self):
        if self.__class__.orgs is None:
            self.__class__.orgs = {}
        self.__class__.orgs[str(self.id)] = self

    def expire_cache(self):
        self.__class__.orgs.pop(str(self.id), None)

    @classmethod
    def get_instance_from_cache(cls, oid):
        if not cls.orgs or not isinstance(cls.orgs, dict):
            return None
        return cls.orgs.get(str(oid))

    @classmethod
    def get_instance(cls, id_or_name, default=False):
        cached = cls.get_instance_from_cache(id_or_name)
        if cached:
            return cached

        if id_or_name is None:
            return cls.default() if default else None
        elif id_or_name in [cls.DEFAULT_ID, cls.DEFAULT_NAME, '']:
            return cls.default()
        elif id_or_name in [cls.ROOT_ID, cls.ROOT_NAME]:
            return cls.root()
        elif id_or_name in [cls.SYSTEM_ID, cls.SYSTEM_NAME]:
            return cls.system()

        try:
            if is_uuid(id_or_name):
                org = cls.objects.get(id=id_or_name)
            else:
                org = cls.objects.get(name=id_or_name)
            org.set_to_cache()
        except cls.DoesNotExist:
            org = cls.default() if default else None
        return org

    def get_org_memebers_by_role(self, role):
        from users.models import User
        if self.is_real():
            return self.members.filter(orgs_through__role=role)
        users = User.objects.filter(role=User.role)
        return users

    @property
    def users(self):
        return self.get_org_memebers_by_role(ROLE.USER)

    @property
    def admins(self):
        return self.get_org_memebers_by_role(ROLE.ADMIN)

    @property
    def auditors(self):
        return self.get_org_memebers_by_role(ROLE.AUDITOR)

    def org_id(self):
        if self.is_real():
            return self.id
        elif self.is_root():
            return self.ROOT_ID
        else:
            return ''

    def get_members(self, exclude=()):
        from users.models import User
        if self.is_real():
            members = self.members.exclude(orgs_through__role__in=exclude)
        else:
            members = User.objects.exclude(role__in=exclude)

        return members.exclude(role=User.ROLE.APP).distinct()

    def can_admin_by(self, user):
        if user.is_superuser:
            return True
        if self.admins.filter(id=user.id).exists():
            return True
        return False

    def can_audit_by(self, user):
        if user.is_super_auditor:
            return True
        if self.auditors.filter(id=user.id).exists():
            return True
        return False

    def can_user_by(self, user):
        if self.users.filter(id=user.id).exists():
            return True
        return False

    def is_real(self):
        return self.id not in (self.DEFAULT_NAME, self.ROOT_ID, self.SYSTEM_ID)

    @classmethod
    def get_user_orgs_by_role(cls, user, role):
        if not isinstance(role, (tuple, list)):
            role = (role, )

        return cls.objects.filter(
            members_through__role__in=role,
            members_through__user_id=user.id
        ).distinct()

    @classmethod
    def get_user_admin_orgs(cls, user):
        if user.is_anonymous:
            return cls.objects.none()
        if user.is_superuser:
            return [*cls.objects.all(), cls.default()]
        return cls.get_user_orgs_by_role(user, ROLE.ADMIN)

    @classmethod
    def get_user_user_orgs(cls, user):
        if user.is_anonymous:
            return cls.objects.none()
        return cls.get_user_orgs_by_role(user, ROLE.USER)

    @classmethod
    def get_user_audit_orgs(cls, user):
        if user.is_anonymous:
            return cls.objects.none()
        if user.is_super_auditor:
            return [*cls.objects.all(), cls.default()]
        return cls.get_user_orgs_by_role(user, ROLE.AUDITOR)

    @classmethod
    def get_user_admin_or_audit_orgs(cls, user):
        if user.is_anonymous:
            return cls.objects.none()
        if user.is_superuser or user.is_super_auditor:
            return [*cls.objects.all(), cls.default()]
        return cls.get_user_orgs_by_role(user, (ROLE.AUDITOR, ROLE.ADMIN))

    @classmethod
    def default(cls):
        return cls(id=cls.DEFAULT_ID, name=cls.DEFAULT_NAME)

    @classmethod
    def root(cls):
        return cls(id=cls.ROOT_ID, name=cls.ROOT_NAME)

    @classmethod
    def system(cls):
        return cls(id=cls.SYSTEM_ID, name=cls.SYSTEM_NAME)

    def is_root(self):
        return self.id is self.ROOT_ID

    def is_default(self):
        return self.id is self.DEFAULT_ID

    def is_system(self):
        return self.id is self.SYSTEM_ID

    def change_to(self):
        from .utils import set_current_org
        set_current_org(self)


class OrganizationMember(models.Model):
    id = models.UUIDField(default=uuid.uuid4, primary_key=True)
    org = models.ForeignKey(Organization, related_name='members_through', on_delete=models.CASCADE, verbose_name=_('Organization'))
    user = models.ForeignKey('users.User', related_name='orgs_through', on_delete=models.CASCADE, verbose_name=_('User'))
    role = models.CharField(max_length=16, choices=ROLE.choices, default=ROLE.USER, verbose_name=_("Role"))
    date_created = models.DateTimeField(auto_now_add=True, verbose_name=_("Date created"))
    date_updated = models.DateTimeField(auto_now=True, verbose_name=_("Date updated"))
    created_by = models.CharField(max_length=128, null=True, verbose_name=_('Created by'))

    class Meta:
        unique_together = [('org', 'user', 'role')]
        db_table = 'orgs_organization_members'

    def __str__(self):
        return '{} is {}: {}'.format(self.user.name, self.org.name, self.role)
