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

    def run(self, args, with_session=False):
        if with_session and self.session_key:
            args.append(f"--session={self.session_key}")
        args.insert(0, 'bw')
        _logger.debug('RUN %s' % ' '.join(args))
        res = pexpect.run(' '.join(args), encoding='utf-8')
        datas = res.splitlines()[-1]
        try:
            return json.loads(datas)
        except Exception as err:
            _logger.error(datas)
            _logger.debug(err)
            pass

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
            if self.api_client_id and self.api_client_secret:
                self.login_with_api_key()
            elif self.username and self.password:
                self.login_with_password()
            else:
                _logger.error('No logging method found')
                return

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
        child.expect(pexpect.EOF)

    def unlock(self):
        child = self.spawn(['unlock', '--raw'])
        child.expect('password')
        child.sendline(self.password)
        child.expect(pexpect.EOF)
        if "Invalid master password." in child.before:
            _logger.error("Invalid master password.")
            return
        self.session_key = child.before.splitlines()[-1]
        os.environ.setdefault('BITWARDEN_SESSION_KEY', self.session_key)

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

    def get_item(self, name, organization_id='', collection_id=''):
        extra_args = []
        if organization_id:
            extra_args.append(f'--organizationid={organization_id}')
        if collection_id:
            extra_args.append(f'--collectionid={collection_id}')
        res = self.search_objects(objects='items', search=name, extra_args=extra_args)
        if res and isinstance(res, list):
            return res[0]
        else:
            return {}

    def get_item_login(self, name):
        res = self.get_item(name)
        if res and isinstance(res, dict):
            return res.get('login', {})

    def get_item_password(self, name):
        res = self.get_item_login(name)
        return res.get('password', '')

    def get_organizations(self):
        return self.search_objects('organizations')

    def get_org_collections(self, search='', organization_id=''):
        if not organization_id:
            organizations = self.get_organizations()
            if organizations:
                organization_id = organizations[0].get('id')
        extra_args = [f'--organizationid={organization_id}']
        return self.search_objects('org-collections',
                                   search=search,
                                   extra_args=extra_args)