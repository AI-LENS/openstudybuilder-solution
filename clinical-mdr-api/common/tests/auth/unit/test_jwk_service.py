"""Test JWT validation with crafted tokens signed with a test JWK"""

# pylint: disable=redefined-outer-name

import logging
import time
from typing import Any, Iterable, Mapping

import authlib.jose.errors
import pytest
from authlib.jose import JsonWebKey, Key, jwt

from common import exceptions
from common.auth.jwk_service import JWKService

# Random-generated with `uuidgen -r`
ISSUER = "b7147eff-ad8e-4b9a-a843-6352c79c7735"
GOOD_AUDIENCE = "13a16f70-189a-407b-a480-596a1a5915e6"
WRONG_AUDIENCE = "a11915fc-4dfb-48e5-8040-e71c6cb2aee4"

JWK_SIGN_KEY_ID = "good-rsa-key"
JWT_SIGN_ALG = "RS256"

# Random-generated with `openssl genrsa 1024`
GOOD_RSA_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQC71YusHGHz1QeRolnzrk/9FxqodCifa23ezq8yKQLk51fUyH7m
NSaPlzoHvMxHrbpmRvl1PVfdIwWDKGczMcAECwV72fWuczEgheWnlUbxACQjOfrx
d0rX9fk7KEFm7efFY0zyWVzEuOFMabisp+YaCwLXmJU1f9MsRNEiCjq+3wIDAQAB
AoGALSNLFkgXzeWilP/DyAhaloJn2JVZcb36QDHA7jfmxyVE+RBZVm7tXlJEErnv
CUaZZZyms+LS64RP/c3Gxwmsj6K9vHDKxlEt+ON7YE3V68hZ78ydrzcsJqj+J6/7
1p2uxOUZDyphbTWl9fe/VsoHV6I7v1Lxm2wAYwVOFlxT1qkCQQDgvPdM6vEbQ3Eg
UfPBRk1VWSz1p1DXjUufH2DzgLYDObST2Yl65Xq8qyNGgkv5UoyAameQQQ5s9Tu2
Se2HAC1lAkEA1fZpKz+VNesVTunGsl4DpgS2qxljdXBfRy8lxfdhIPL6O/x3r7kl
CU9xhptUKNxQ1frebN304nZxmA1D+wqI8wJAIS8l4QCr+1eZA6m2MWq9DoYtYlSD
VmCxstxCR5JQzeceZ9puN2xdFDC887NXnof24RtVEXLZu3L2jzMZVJ7NFQJBAMDo
ecnUeeMzIPMVM2B+Aywb89Yv/cxUlJLJn3TtpVTfvV14MzDr7MiIKAME6MwuV3OV
zBS7yZ6ky6Ybz773sKECQQCWgyugb9CUHik2gOYzxS5hc9lUqPM2ywUg4GWIIcG4
yNKsZumEv5bJPfBUzzgL3KxbUGQJcFHQNVLL7hOnIT2m
-----END RSA PRIVATE KEY-----
"""
WRONG_RSA_KEY = """
-----BEGIN RSA PRIVATE KEY-----
MIICXQIBAAKBgQDDdXFNlTGkrLsw1+AXKbxvZTHrv8Bdnbes7N6PmzDUu+TaPR8u
JneqkTrbe3jYymaJC2+zalO48/y2UX7eSBOiHPpSZAg0mGIWX21UjL36rWtLHVi4
adWcBYz+AQDvRGW1D2IKaPuwChKarYFqGW9u7d6CKlpuBndb7EHJknu8zQIDAQAB
AoGAX0Owc4XR6lcd7VJqMB/xbcG+sQ6GbZpfWXMhjpCvHiBuDEhaGB47mPCr5Smq
3s7XZtgiGyopoC2a8CmMUj6DAlgQQst+uusZiBxOYye9PbW84X9D2kbogAhtZ1P/
mCc+ysDQFk7xq/e7qdCErh0toKBlUx7k41y/rW8XyZbdEmkCQQDrp5vmDNzKfaXt
8fTnmDupvvI3zB9PD9hLge7v0vVIRogxltIi8ru7Id2/qMtYIV7jX0Dl9nLJErCD
6p8pqKnHAkEA1FVuULQbR6lUlgpK/6kLZqXckv0gLOEN8yjDPQsxNtg7DiWRDNwI
mx0Hp7L2e7V3t3um/Fsdg0mgiKEWEDoEywJBAN+9CBB4n9yFRVhQRFTqvaLhjzmY
zRUUlyjBmakLoyRXCxIB/0t9KO54LgC9cyseq+e21XhA8CSmYP8ucKVt5JsCQFkX
R2QhTdjxmYYi53kCCsCVE0mxX5C1FU9TaSfxzEKA07aJ2KSWph2/PnkExBr/9y1L
erMj3+w4Nl1diY5haaUCQQDjnPpYEWVzc5Akms7lM+BUwajdUHjh8qGPvhtdU6nm
XlyuOhOyd50GXmwyzbwCD9f5h0UqkbSpSaJYOrUxO+pN
-----END RSA PRIVATE KEY-----
"""

SCOPES = ("API.call",)

# Payload is similar to what Azure Active Directory provides, but the IDs are random-generated
CLAIMS_TEMPLATE = (
    ("aud", GOOD_AUDIENCE),
    ("iss", ISSUER),
    ("iat", 0),
    ("nbf", 0),
    ("exp", 0),
    (
        "aio",
        "ATQAy/wjvI8cYyofgA5hI54Mtv0L0ITDpd1nTTVc/HSJQZR3h3vQcb9idvgnyKLpnpEEHN3Ki01K",
    ),
    ("azp", ISSUER),
    ("azpacr", "1"),
    ("name", "Test User 42"),
    ("oid", "6bbbbf12-804f-48d8-93e5-4e40ffc43609"),
    ("preferred_username", "testuser42@5ehk46MAfUHRc2Ku.onmicrosoft.com"),
    ("rh", "0.yeyjnjd_5J_Un5NUpkzXAR0iiMlRETvasxgZ8UmkOF_47hd91Nk."),
    ("scp", " ".join(SCOPES)),
    ("sub", "XM-To3xy0J_FYqWuUgRiWNOVT0gGDIlRoHlA3Cw6o9E"),
    ("tid", "744ed15a-23b8-4635-a0e2-e3f7fc61916c"),
    ("uti", "26BGGwABmKH4DMNSWu5DYN"),
    ("ver", "2.0"),
)

log = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def jwk_good_key():
    key = dict(JsonWebKey.import_key(GOOD_RSA_KEY, {"kty": "RSA"}))
    key["kid"] = "good-rsa-key"
    key["use"] = "sig"
    key["issuer"] = ISSUER
    return key


@pytest.fixture(scope="session")
def jwk_wrong_key():
    key = dict(JsonWebKey.import_key(WRONG_RSA_KEY, {"kty": "RSA"}))
    key["kid"] = "wrong-rsa-key"
    key["use"] = "sig"
    key["issuer"] = ISSUER
    return key


@pytest.fixture(scope="session")
def jwk_service(jwk_good_key):
    oauth_client = MockOauthClient(
        metadata={
            "issuer": ISSUER,
            "jwks_uri": "fetch_jwk_set is monkey patched",
        }
    )

    log.debug("Creating JWKService with MockOauthClient")
    service = JWKService(oauth_client, audience=GOOD_AUDIENCE)

    log.debug("Patching JWKService._fetch_json() on instance")

    # pylint: disable=unused-argument
    async def return_jwks_doc(url):
        return {"keys": [jwk_good_key]}

    setattr(service, "_fetch_json", return_jwks_doc)

    return service


class MockOauthClient:
    """Mock OauthClient for clinical_mdr_api.auth.jwk_service.JWKService"""

    def __init__(self, metadata):
        self._metadata = metadata

    async def load_server_metadata(self):
        return self._metadata


def mk_claims(
    now: int | float | None = None,
    exp: int | float = 300,
    audience: str | None = GOOD_AUDIENCE,
    issuer: str | None = ISSUER,
    scopes: Iterable[str] = SCOPES,
) -> dict[str, Any]:
    if now is None:
        now = time.time()

    claims = dict(CLAIMS_TEMPLATE)
    claims["iat"] = int(now)
    claims["nbf"] = claims["iat"]
    claims["exp"] = int(now + exp)

    claims["aud"] = audience
    claims["iss"] = issuer
    claims["azp"] = claims["iss"]

    claims["scp"] = " ".join(scopes)

    return claims


def mk_jwt(claims: Mapping, key: Key) -> bytes:
    header = {"alg": JWT_SIGN_ALG}
    return jwt.encode(header, claims, key)


# pylint: disable=unused-argument
@pytest.mark.asyncio
async def test_correct_test_setup(jwk_service, jwk_good_key, jwk_wrong_key):
    """This tests if test setup is correct, other tests rely on this"""

    log.debug("Creating claims")
    claims_in = mk_claims()
    log.debug("Creating token from claims: %s", claims_in)
    token = mk_jwt(claims_in, jwk_good_key)

    log.info("Test JWT: %s", token)

    log.debug("Decoding JWT")
    claims = jwt.decode(token, jwk_good_key)
    assert claims == claims_in, "Claims doesn't match after encoding-decoding cycle"

    log.debug("Validating claims: %s", claims)
    claims.validate()

    log.debug("Same with wrong-key should work too")
    token = mk_jwt(claims_in, jwk_wrong_key)
    claims = jwt.decode(token, jwk_wrong_key)
    claims.validate()
    assert (
        claims == claims_in
    ), "Claims doesn't match after encoding-decoding cycle with wrong-key"


@pytest.mark.asyncio
async def test_good_signing_key(jwk_service, jwk_good_key):
    claims_in = mk_claims()
    token = mk_jwt(claims_in, jwk_good_key)
    claims = await jwk_service.validate_jwt(token)
    assert claims == claims_in, "Claims differ"


@pytest.mark.asyncio
async def test_wrong_signing_key(jwk_service, jwk_wrong_key):
    claims = mk_claims()
    token = mk_jwt(claims, jwk_wrong_key)
    with pytest.raises(exceptions.NotAuthenticatedException):
        # Expected to raise NotAuthenticatedException exception
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_invalid_signature(jwk_service, jwk_good_key):
    claims = mk_claims()
    token: str | bytes | list[str]
    token = mk_jwt(claims, jwk_good_key)

    # change payload part of token #
    claims["scp"] += " God.Mode"
    token2 = mk_jwt(claims, jwk_good_key)
    payload2 = token2.decode("utf8").split(".", 2)[1]
    token = token.decode("utf8").split(".", 2)
    token[1] = payload2
    token = ".".join(token)

    with pytest.raises(authlib.jose.errors.BadSignatureError):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_expired(jwk_service, jwk_good_key):
    exp = 300
    now = time.time() - exp - jwk_service.leeway - 1
    claims = mk_claims(now=now, exp=exp)
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.ExpiredTokenError):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_not_before(jwk_service, jwk_good_key):
    exp = 300
    claims = mk_claims(exp=exp)
    claims["nbf"] = int(time.time() + 60)
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.InvalidTokenError, match="not valid yet"):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_invalid_audience(jwk_service, jwk_good_key):
    claims = mk_claims(audience="pink-panther")
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.InvalidClaimError, match='"aud"'):
        await jwk_service.validate_jwt(token)


@pytest.mark.asyncio
async def test_token_invalid_issuer(jwk_service, jwk_good_key):
    claims = mk_claims(issuer="pink-panther-social-club")
    token = mk_jwt(claims, jwk_good_key)
    with pytest.raises(authlib.jose.errors.InvalidClaimError, match='"iss"'):
        await jwk_service.validate_jwt(token)
