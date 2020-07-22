from django.utils.translation import ugettext_lazy as _

from common.db.models import ChoiceSet


class ROLE(ChoiceSet):
    ADMIN = 'Admin', _('Administrator')
    USER = 'User', _('User')
    AUDITOR = 'Auditor', _("Auditor")
