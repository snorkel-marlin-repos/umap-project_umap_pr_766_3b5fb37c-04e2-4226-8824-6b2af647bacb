import socket

import pytest
from django.conf import settings
from django.contrib.auth import get_user, get_user_model
from django.urls import reverse
from django.test import RequestFactory

from umap.views import validate_url


def get(target="http://osm.org/georss.xml", verb="get", **kwargs):
    defaults = {
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        'HTTP_REFERER': '%s/path/' % settings.SITE_URL
    }
    defaults.update(kwargs)
    func = getattr(RequestFactory(**defaults), verb)
    return func('/', {'url': target})


def test_good_request_passes():
    target = "http://osm.org/georss.xml"
    request = get(target)
    url = validate_url(request)
    assert url == target


def test_no_url_raises():
    request = get("")
    with pytest.raises(AssertionError):
        validate_url(request)


def test_relative_url_raises():
    request = get("/just/a/path/")
    with pytest.raises(AssertionError):
        validate_url(request)


def test_file_uri_raises():
    request = get("file:///etc/passwd")
    with pytest.raises(AssertionError):
        validate_url(request)


def test_localhost_raises():
    request = get("http://localhost/path/")
    with pytest.raises(AssertionError):
        validate_url(request)


def test_local_IP_raises():
    url = "http://{}/path/".format(socket.gethostname())
    request = get(url)
    with pytest.raises(AssertionError):
        validate_url(request)


def test_POST_raises():
    request = get(verb="post")
    with pytest.raises(AssertionError):
        validate_url(request)


def test_unkown_domain_raises():
    request = get("http://xlkjdkjsdlkjfd.com")
    with pytest.raises(AssertionError):
        validate_url(request)


def test_valid_proxy_request(client):
    url = reverse('ajax-proxy')
    params = {'url': 'http://example.org'}
    headers = {
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        'HTTP_REFERER': settings.SITE_URL
    }
    response = client.get(url, params, **headers)
    assert response.status_code == 200
    assert 'Example Domain' in response.content.decode()
    assert 'Cookie' not in response['Vary']


def test_valid_proxy_request_with_ttl(client):
    url = reverse('ajax-proxy')
    params = {'url': 'http://example.org', 'ttl': 3600}
    headers = {
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        'HTTP_REFERER': settings.SITE_URL
    }
    response = client.get(url, params, **headers)
    assert response.status_code == 200
    assert 'Example Domain' in response.content.decode()
    assert 'Cookie' not in response['Vary']
    assert response['X-Accel-Expires'] == '3600'


def test_valid_proxy_request_with_invalid_ttl(client):
    url = reverse('ajax-proxy')
    params = {'url': 'http://example.org', 'ttl': 'invalid'}
    headers = {
        'HTTP_X_REQUESTED_WITH': 'XMLHttpRequest',
        'HTTP_REFERER': settings.SITE_URL
    }
    response = client.get(url, params, **headers)
    assert response.status_code == 200
    assert 'Example Domain' in response.content.decode()
    assert 'Cookie' not in response['Vary']
    assert 'X-Accel-Expires' not in response


@pytest.mark.django_db
def test_login_does_not_contain_form_if_not_enabled(client, settings):
    settings.ENABLE_ACCOUNT_LOGIN = False
    response = client.get(reverse('login'))
    assert 'username' not in response.content.decode()


@pytest.mark.django_db
def test_login_contains_form_if_enabled(client, settings):
    settings.ENABLE_ACCOUNT_LOGIN = True
    response = client.get(reverse('login'))
    assert 'username' in response.content.decode()


@pytest.mark.django_db
def test_can_login_with_username_and_password_if_enabled(client, settings):
    settings.ENABLE_ACCOUNT_LOGIN = True
    User = get_user_model()
    user = User.objects.create(username='test')
    user.set_password('test')
    user.save()
    client.post(reverse('login'), {'username': 'test', 'password': 'test'})
    user = get_user(client)
    assert user.is_authenticated
