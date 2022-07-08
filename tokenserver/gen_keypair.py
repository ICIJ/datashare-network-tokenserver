from typing import Tuple

from sscred import AbePrivateKey, AbeParam, AbePublicKey, packb


def gen_keypair() -> Tuple[AbePrivateKey, AbePublicKey]:
    return AbeParam().generate_new_key_pair()


if __name__ == '__main__':
    skey, _ = gen_keypair()
    print(packb(skey).hex())