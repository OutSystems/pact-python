We had to use this forked version because the message provider does not support pact broker.

There is an open PR https://github.com/pact-foundation/pact-python/pull/257 to solve this.

To have this working we needed to run `make package` and upload the generated file `dist/pact-python-1.4.2.tar.gz` to the new created release `v1.4.2`.

To use it you need to add to the requirements `https://github.com/OutSystems/pact-python/releases/download/v1.4.2/pact-python-1.4.2.tar.gz` instead of `pact-python==1.4.2`