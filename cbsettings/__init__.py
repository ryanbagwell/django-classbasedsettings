import django
from django.utils.importlib import import_module
import imp
import os
import sys
from cbsettings.exceptions import InvalidSettingsFactory, SettingsFactoryDoesNotExist
from cbsettings.settings import DjangoDefaults
from cbsettings.switching import switcher
from cbsettings.version import *


ENVIRONMENT_VARIABLE = 'DJANGO_SETTINGS_FACTORY'
DJANGO_SETTINGS_MODULE = django.conf.ENVIRONMENT_VARIABLE


def configure(factory=None, **kwargs):
    if not factory:
        factory = os.environ.get(ENVIRONMENT_VARIABLE)
        if not factory:
            raise ImportError('Settings could not be imported because'
                    ' configure was called without arguments and the environment'
                    ' variable %s is undefined.' % ENVIRONMENT_VARIABLE)
    if '.' in factory:
        factory_module, factory_name = factory.rsplit('.', 1)
        try:
            mod = import_module(factory_module)
            factory_obj = getattr(mod, factory_name)
        except (ImportError, AttributeError), err:
            raise SettingsFactoryDoesNotExist('The object "%s" could not be'
                    ' found (Is it on sys.path?): %s' % (factory, err))

        settings_obj = factory_obj()
        settings_dict = dict((k, getattr(settings_obj, k)) for k in
                dir(settings_obj) if not str(k).startswith('_'))

        if 'SETTINGS_MODULE' not in settings_dict:
            settings_dict['SETTINGS_MODULE'] = '%s_%s_unrolledcbsettings' % (
                    factory_module, factory_name)

        # Create the settings module.
        parts = settings_dict['SETTINGS_MODULE'].split('.')
        for module_name in map(lambda x: '.'.join(x), [parts[0:i + 1] for i in
                range(len(parts))]):
            try:
                module = __import__(module_name, fromlist=[''])
            except ImportError:
                module = imp.new_module(module_name)
                sys.modules[module_name] = module

        # Unroll the settings into a new module.
        for k, v in settings_dict.items():
            setattr(module, k, v)

        os.environ[DJANGO_SETTINGS_MODULE] = settings_dict['SETTINGS_MODULE']

        return mod, settings_obj
    else:
        raise InvalidSettingsFactory('%s is not a valid settings factory.'
            ' Please provide something of the form'
            ' `path.to.MySettingsFactory`' % factory)
