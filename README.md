# datashare-network-tokenserver [![CircleCI](https://circleci.com/gh/ICIJ/datashare-network-tokenserver/tree/main.svg?style=svg)](https://circleci.com/gh/ICIJ/datashare-network-tokenserver/tree/main)

A server to issue tokens based on blind signature

It is based on springlab@EPFL [SScred](https://github.com/spring-epfl/SSCred) based itself on [petlib](https://github.com/gdanezis/petlib) and itelf based on [openssl](https://www.openssl.org/).

## Endpoints

All endpoints should be secured with HTTPS (TLS).

### Public endpoints

* `GET /publickey`

### Authenticated endpoints

Those endpoints are protected with JWT

* `POST /commitments?uid=foo&number=3`
  * parameters : 
    * number: (int) number of token to generate
    * uid: (string) user id
  * returns a commitment list msg pack encoded
* `POST /tokens?uid=foo`
  * parameters :
    * uid: (string) user id
    * payload: list of pretokens msg pack encoded
    * returns a token list msg pack encoded