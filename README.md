# datashare-network-tokenserver

A server to issue tokens based on blind signature

It is based on springlab@EPFL [SScred](https://github.com/spring-epfl/SSCred) based itself on [petlib](https://github.com/gdanezis/petlib) and itelf based on [openssl](https://www.openssl.org/).

## Endpoints

All endpoints should be secured with HTTPS (TLS).

### Public endpoints

* `GET /publickey`

### Authenticated endpoints

Those endpoints are protected with JWT

* `GET /commitment`
* `GET /blind_token
