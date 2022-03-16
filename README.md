# datashare-network-tokenserver [![CircleCI](https://circleci.com/gh/ICIJ/datashare-network-tokenserver/tree/main.svg?style=svg)](https://circleci.com/gh/ICIJ/datashare-network-tokenserver/tree/main)

A server to issue tokens based on blind signature

It is based on springlab@EPFL [SScred](https://github.com/spring-epfl/SSCred) based itself on [petlib](https://github.com/gdanezis/petlib) and itelf based on [openssl](https://www.openssl.org/).

It is supposed to be secured behind an SSO/OAuth2 server.

## Configuration 

Configuration is provided with environment variables :

* TOKEN_SERVER_REDIS_URL: redis url (default: `redis://redis`)
* TOKEN_SERVER_REDIS_TTL: time to live for commitments internal parameters (default 30s)
* TOKEN_SERVER_SKEY: master secret key for the server encoded in [msgpack](https://msgpack.org/) hex string

## Endpoints

All endpoints should be secured with HTTPS (TLS).

* `GET /publickey`
  * returns the server public key
* `POST /commitments?uid=foo&number=3`
  * parameters : 
    * number: (int) number of token to generate
    * uid: (string) user id
  * returns a commitment list msg pack encoded
* `POST /pretokens?uid=foo`
  * parameters :
    * uid: (string) user id
    * payload: list of pretokens msg pack encoded
    * returns a token list msg pack encoded
