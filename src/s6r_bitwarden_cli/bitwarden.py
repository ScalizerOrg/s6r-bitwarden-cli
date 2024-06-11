import json
import logging
import pexpect
import os

_logger = logging.getLogger(__name__)
c_handler = logging.StreamHandler()
_logger.addHandler(c_handler)


class BitwardenCli:

    def __init__(self, username='', password='', api_client_id='', api_client_secret='', verbose=False):
        self.username = username or os.environ.get('BITWARDEN_USERNAME', '')
        self.password = password or os.environ.get('BITWARDEN_PASSWORD', '')
        self.api_client_id = api_client_id or os.environ.get('BITWARDEN_API_CLIENT_ID', '')
        self.api_client_secret = api_client_secret or os.environ.get('BITWARDEN_API_CLIENT_SECRET', '')
        self.session_key = os.environ.get('BITWARDEN_SESSION_KEY', '')
        self.verbose = verbose

        self.set_logger()

    def spawn(self, args):
        _logger.debug('SPAWN bw %s' % ' '.join(args))
        return pexpect.spawn('bw', args, encoding='utf-8')

    def run(self, args, with_session=False, retry=False):
        if with_session and self.session_key:
            args.append(f"--session={self.session_key}")
        if args and args[0] != 'bw':
            args.insert(0, 'bw')
        _logger.debug('RUN %s' % ' '.join(args))
        res = pexpect.run(' '.join(args), encoding='utf-8')
        datas = res.splitlines()[-1]
        try:
            return json.loads(datas)
        except Exception as err:
            _logger.debug(err)
            self.handle_error(datas)
            if not retry:
                return self.run(args, with_session, retry=True)

    def handle_error(self, error):
        if 'Vault is locked' in error:
            return self.unlock()
        if 'You are not logged in' in error:
            return self.login()
        raise ConnectionError(error)

    def set_logger(self, level=None):
        if level:
            _logger.setLevel(level)
        if self.verbose:
            _logger.setLevel(logging.DEBUG)

    def get_status(self):
        args = ['status']
        if self.session_key:
            args.append(f"--session={self.session_key}")
        values = self.run(args)
        return values.get('status', '')

    def is_locked(self):
        return self.get_status() == 'locked'

    def login(self):
        status = self.get_status()
        if status == 'unlocked':
            return True
        if status == 'locked':
            return self.unlock()

        if status == 'unauthenticated':
            self.session_key = ''
            if self.api_client_id and self.api_client_secret:
                self.login_with_api_key()
            elif self.username and self.password:
                self.login_with_password()
            else:
                raise ConnectionError('No logging method found.')

        if self.is_locked():
            self.unlock()

    def login_with_api_key(self):
        args = ['login', '--apikey', '--raw']
        child = self.spawn(args)
        child.expect('client_id')
        child.sendline(self.api_client_id)
        child.expect('client_secret')
        child.sendline(self.api_client_secret)
        child.expect(pexpect.EOF)

    def login_with_password(self):
        args = ['login', '--raw']
        child = self.spawn(args)
        child.expect('Email address')
        child.sendline(self.username)
        child.expect('Master password')
        child.sendline(self.password)
        i = child.expect(['Two-step login code:', pexpect.EOF])
        if i == 0:
            child.sendline(input('Bitwarden two-step login code:'))
            child.expect(pexpect.EOF)

    def logout(self):
        args = ['logout']
        child = self.spawn(args)
        child.expect(pexpect.EOF)

    def unlock(self):
        if not self.password:
            raise ConnectionError("Bitwarden master password required.")
        child = self.spawn(['unlock', '--raw'])
        child.expect('password')
        child.sendline(self.password)
        child.expect(pexpect.EOF)
        if "Invalid master password." in child.before:
            raise ConnectionRefusedError("Invalid Bitwarden master password.")
        self.session_key = child.before.splitlines()[-1]

    def search_objects(self, objects='items', search='', extra_args=None):
        """
        Search objects in Bitwarden using 'bw list' command
        :param objects: valid values: items, folders, collections, org-collections, org-members, organizations
        :param search: a string to find in item name
        :param extra_args: a list of argument to add in bw command
        :return: a list of objects
        """
        args = ['list', objects, '--raw', '--nointeraction']
        if search:
            args.append(f'--search="{search}"')
        if extra_args:
            args.extend(extra_args)
        return self.run(args, with_session=True) or []

    def get_item(self, name, organization_id='', collection_id='', collection_name=''):
        extra_args = []
        if organization_id:
            extra_args.append(f'--organizationid={organization_id}')
        if collection_name and not collection_id:
            collection_id = self.get_org_collection_id(collection_name)
        if collection_id:
            extra_args.append(f'--collectionid={collection_id}')
        res = self.search_objects(objects='items', search=name, extra_args=extra_args)
        if res and isinstance(res, list):
            return res[0]
        else:
            return {}

    def get_item_login(self, name, organization_id='', collection_id='', collection_name=''):
        res = self.get_item(name, organization_id, collection_id, collection_name)
        if res and isinstance(res, dict):
            return res.get('login', {})
        return {}

    def get_item_fields(self, name, organization_id='', collection_id='', collection_name=''):
        res = self.get_item(name, organization_id, collection_id, collection_name)
        if res and isinstance(res, dict):
            return res.get('fields', [])
        return []

    def get_item_field(self, name, field_name, organization_id='', collection_id='', collection_name=''):
        fields = self.get_item_fields(name, organization_id, collection_id, collection_name)
        for field in fields:
            if field.get('name') == field_name:
                return field.get('value', '')
        return ''

    def get_item_password(self, name, organization_id='', collection_id='', collection_name=''):
        res = self.get_item_login(name, organization_id, collection_id, collection_name)
        return res.get('password', '')

    def get_item_username(self, name, organization_id='', collection_id='', collection_name=''):
        res = self.get_item_login(name, organization_id, collection_id, collection_name)
        return res.get('username', '')

    def get_organizations(self):
        return self.search_objects('organizations')

    def get_default_organization(self):
        organizations = self.get_organizations()
        return organizations[0] if organizations else False

    def get_default_organization_id(self, retry=0):
        organization = self.get_default_organization()
        if not organization and retry < 3:
            _logger.info("Retry Bitwarden get_default_organization_id ...")
            return self.get_default_organization_id(retry=retry + 1)
        return organization.get('id') if organization else False

    def get_org_collections(self, search='', organization_id=''):
        extra_args = []
        if not organization_id:
            organization_id = self.get_default_organization_id()
        if organization_id:
            extra_args.append(f'--organizationid={organization_id}')
        return self.search_objects('org-collections',
                                   search=search,
                                   extra_args=extra_args)

    def get_org_collection(self, search='', organization_id=''):
        collections = self.get_org_collections(search, organization_id)
        return collections[0] if collections else False

    def get_org_collection_id(self, search='', organization_id='', retry=0):
        collection = self.get_org_collection(search, organization_id)
        if not collection and retry < 3:
            _logger.info("Retry Bitwarden get_org_collection_id ...")
            return self.get_org_collection_id(search, organization_id, retry + 1)
        return collection.get('id') if collection else False
