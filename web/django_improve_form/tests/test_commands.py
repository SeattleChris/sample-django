from django.test import TestCase  # , TransactionTestCase, Client, RequestFactory,
from unittest import skip
from django.core.management import call_command
from .helper_admin import APP_NAME
# from django.contrib.auth import get_user_model
from .helper_admin import AdminSetupTests  # , AdminModelManagement
from .helper_views import MimicAsView, USER_DEFAULTS
from .helper_general import AnonymousUser, UserModel  # , MockRequest, MockUser, MockStaffUser, MockSuperUser
from ..views import RegisterSimpleFlowView, RegisterActivateFlowView, ModifyUser
from ..views import RegisterModelSimpleFlowView, RegisterModelActivateFlowView
from ..forms import RegisterUserForm, RegisterChangeForm, RegisterModelForm
from project.management.commands.urllist import Command as urllist
# from django.conf import settings
# from django.core.exceptions import ObjectDoesNotExist
# from django.db.models import Q, Max, Subquery
# from django.urls import reverse
# from datetime import date, time, timedelta, datetime as dt
from pprint import pprint

# Create your tests here.


class UrllistTests(TestCase):

    def test_get_col_names(self):
        """Confirm it processes correctly when the 'only' parameter has an integer value. """
        priorities = urllist.column_priority
        all_cols = urllist.all_columns
        max_value = len(priorities)

        for i in range(max_value):
            expected = [ea for ea in all_cols if ea in priorities[:i]]
            urls = call_command('urllist', APP_NAME, only=i, long=True, data=True)
            # actual =