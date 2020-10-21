from django.utils.module_loading import import_string
from unittest import skip

UserModel = import_string('django.contrib.auth.models.User')
AnonymousUser = import_string('django.contrib.auth.models.AnonymousUser')


class MockRequest:
    pass


class MockUser:
    is_active = True
    is_authenticated = True
    is_anonymous = False
    is_staff = False
    is_superuser = False


class MockStaffUser(MockUser):
    is_staff = True
    is_superuser = False


class MockSuperUser(MockUser):
    is_staff = True
    is_superuser = True

    def has_perm(self, perm):
        return True


class CommandUtilitiesTests:

    @skip("Not Implemented")
    def test_createsu_command(self):
        """Our custom command to create a Superuser as an initial admin. """
        # TODO: Write tests for when there is no superuser.
        # This seemed to not work when using this command on PythonAnywhere the first time
        pass

    @skip("Not Implemented")
    def test_urllist_command(self):
        """Our custom command to list all url names installed for the Django application. """
        # TODO: Write tests for when there is no superuser.
        # This seemed to not work when using this command on PythonAnywhere the first time
        pass
