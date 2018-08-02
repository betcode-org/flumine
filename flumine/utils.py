import uuid


def create_short_uuid():
    return str(uuid.uuid4())[:8]


def login_no_certs(betting_client):
    """Betfair login with no certs.
    """
    url = '%s%s' % (betting_client.identity_uri, 'login')
    headers = {
        'Accept': 'application/json',
        'X-Application': betting_client.app_key,
        'content-type': 'application/x-www-form-urlencoded',
    }
    response = betting_client.session.post(
        url, data=betting_client.login.data, headers=headers
    )
    response_json = response.json()
    betting_client.set_session_token(response_json.get('token'))
