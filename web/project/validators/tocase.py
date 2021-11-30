from typing import Dict, List, Optional, Sequence, TypeVar, Any, Union
from django.db import models
from django.core.exceptions import ImproperlyConfigured, ValidationError, NON_FIELD_ERRORS
from django.core.validators import (MaxValueValidator, BaseValidator, )
from django.utils.translation import gettext as _, gettext_lazy as _z


class ToCaseValidator(BaseValidator):
    code = "to_case"  # concatenate with transform name e.g. _upper, _lower, etc
    _valid_values = {  # param, error_code, limit_method
        'upper': (_('uppercased'), '_upper'),
        'lower': (_('lowercased'), '_lower'),
        'capital': (_('capitalized'), '_capital'),
        'casefold': (_('casefolded'), '_casefold'),
        }
    InvalidValue = ValueError(_(
        "ToCaseValidator must be set with one of {}.".format(
            ', '.join(_valid_values.keys()))
        ))

    def __init__(self, limit_value: Any) -> None:
        limit_value, _transform = self._valid_values.get(limit_value, ('', ''))
        if limit_value == '':
            raise self.InvalidValue
        self.code = self.code + str(_transform)
        self._transform = _transform
        super().__init__(limit_value, message=None)

    def __eq__(self, other):
        default = super().__eq__(other)  # limit_value, message, code
        if default is NotImplemented:
            return NotImplemented
        return default and self._transform == other._transform

    def _bad_transform(self, x: str, check: bool = True) -> Union[str, bool]:
        raise ImproperlyConfigured(_("Transform method unassigned"))

    def _upper(self,    x: str, check: bool = True) -> Union[str, bool]:
        return x.isupper() if check else x.upper()

    def _lower(self,    x: str, check: bool = True) -> Union[str, bool]:
        return x.islower() if check else x.lower()

    def _capital(self,  x: str, check: bool = True) -> Union[str, bool]:
        words = x.split()
        if check:
            upper_chars = ''.join(word[0] for word in words)
            lower_chars = ''.join(word[1:] for word in words)
            return upper_chars.isupper() and lower_chars.islower()
        return ' '.join(word.capitalize() for word in words)

    def _casefold(self, x: str, check: bool = True) -> Union[str, bool]:
        return x.casefold() == x if x else x.casefold()

    def transform(self, value: str, check: bool = True) -> Union[str, bool]:
        """Uses initialized transform function, verifying on check is True. """
        callback = getattr(self, self._transform, self._bad_transform)
        if callable(self._transform):
            callback = self._transform
        result = callback(value, check=check)
        return result

    def compare(self, val: Any, limit_value: str) -> bool:
        "Returns True if val is not valid. "
        is_valid = None
        if val is None:
            is_valid = True
        elif not isinstance(val, str):
            is_valid = False
        else:
            is_valid = self.transform(val, check=True)
        return not is_valid if isinstance(is_valid, bool) else True

    def clean(self, x: Any) -> Any:
        if isinstance(x, str):
            x = self.transform(x, check=False)
        return super().clean(x)
