# s6r-bitwarden-cli

Interact easily with Bitwarden client.

## Overview

s6r-bitwarden-cli is a Python script designed to provide a convenient interface for interacting with the
Bitwarden command-line interface (CLI) tool. It allows users to perform various Bitwarden actions, such as logging in,
searching for items, retrieving item details, collections, organizations, directly from within a Python script.


## Table of Contents

- [Installation](#installation)
    - [Install s6r-bitwarden-cli](#install-s6r-bitwarden-cli)
    - [Install Bitwarden CLI](#install-bitwarden-cli)
- [Usage](#usage)
- [Login to Bitwarden Vault](#login-to-bitwarden-vault)
    - [Login with Username and Password](#login-with-username-and-password)
    - [Login with API Key](#login-with-api-key)
    - [Unlock with Session Key](#unlock-with-session-key)
- [Examples](#examples)
- [License](#license)
- [Contributing](#contributing)
- [Contributors](#contributors)
- [Maintainer](#maintainer)




## Installation

```bash
    pip install s6r-bitwarden-cli
```

Make sure you have already logged for the first time with `bw`:

```bash
bw login
```


### Install Bitwarden CLI

Make sure to install the Bitwarden CLI tool on your system. 
You can download it from the official Bitwarden website or use your package manager.

[Download and install](https://bitwarden.com/help/cli/#download-and-install)


## Usage

```python
from s6r_bitwarden_cli import BitwardenCli

bw_cli = BitwardenCli()
password = bw_cli.get_item_password('Staging', collection_name='My collection')
```

The `get_item_password` method, when used with correctly set environment variables, abstracts the complexities of
Bitwarden authentication and CLI interactions, providing a seamless way to retrieve passwords for specified items.

## Login to Bitwarden Vault

To log in to your Bitwarden Vault, you have multiple options based on your preferred authentication method.

### Login with Username and Password

Set the following environment variables to log in using your Bitwarden username and password:

- `BITWARDEN_USERNAME`: Your Bitwarden username.
- `BITWARDEN_PASSWORD`: Your Bitwarden password.

```bash
export BITWARDEN_USERNAME=your_username
export BITWARDEN_PASSWORD=your_password
```

### Login with API Key

If you prefer to use an API key for authentication, set the following environment variables:

- `BITWARDEN_API_CLIENT_ID`: Your Bitwarden API client ID.
- `BITWARDEN_API_CLIENT_SECRET`: Your Bitwarden API client secret.

Note: The `BITWARDEN_PASSWORD` environment variable is still required to unlock the vault, even when using API key
authentication.

```bash
export BITWARDEN_API_CLIENT_ID=your_api_client_id
export BITWARDEN_API_CLIENT_SECRET=your_api_client_secret
```

### Unlock with Session Key

If you are already logged in and have a session key, 
set the BITWARDEN_SESSION_KEY environment variable to unlock the vault.

This method allows you to bypass the username and password or API key authentication if you have an active session.

```bash
export BITWARDEN_SESSION_KEY=your_session_key
```

## Examples
```python
# Initialize Bitwarden CLI
from s6r_bitwarden_cli import BitwardenCli
bw = BitwardenCli(username='your_username', password='your_password', verbose=True)

# Check Bitwarden session status
status = bw.get_status()

# Perform login
bw.login()

# Unlock Bitwarden vault
bw.unlock()

# Search for Bitwarden items
items = bw.search_objects(objects='items', search='keyword')

# Retrieve details of a Bitwarden item
item_details = bw.get_item(name='item_name')

# Get username of a Bitwarden item
username = bw.get_item_username(name='item_name')

# Get value of a custom field of a Bitwarden item
my_custom_field = bw.get_item_field(name='item_name', field_name='my_custom_field')

# Get a list of Bitwarden organizations
organizations = bw.get_organizations()

# Get the default organization
default_organization = bw.get_default_organization()

# Get the ID of the default organization
default_organization_id = bw.get_default_organization_id()

# Get organization collections
org_collections = bw.get_org_collections(search='collection_name', organization_id='organization_id')

# Get an organization collection
org_collection = bw.get_org_collection(search='collection_name', organization_id='organization_id')

# Get the ID of an organization collection
org_collection_id = bw.get_org_collection_id(search='collection_name', organization_id='organization_id')

# logout from Bitwarden
bw.logout()
```

## License

This project is licensed under the [GNU Lesser General Public License (LGPL) Version 3](https://www.gnu.org/licenses/lgpl-3.0.html).


## Contributing

Contributions are welcome! If you find any issues or have suggestions for improvements,
please open an issue or submit a pull request.

- GitHub Repository: [ScalizerOrg/s6r-bitwarden-cli](https://github.com/ScalizerOrg/s6r-bitwarden-cli)

## Contributors

* Michel Perrocheau - [Github](https://github.com/myrrkel)


## Maintainer

This software is maintained by [Scalizer](https://www.scalizer.fr).


<div style="text-align: center;">

[![Scaliser](./logo_scalizer.png)](https://www.scalizer.fr)

</div>
