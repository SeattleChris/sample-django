from django.utils.module_loading import import_string

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
