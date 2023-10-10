#!/bin/bash

python3 -c "import secrets; print('session_secret=b\\'{}\\''.format(secrets.token_hex()))" > app_secrets.py
