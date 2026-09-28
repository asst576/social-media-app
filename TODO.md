# TODO

- [ ] During the explicit `sync docs` phase, add living documentation under `doc/wiki/` and record operational footguns under `doc/wiki/footguns/`.
- [ ] Before public deployment, configure a production secret, disable debug mode, set allowed hosts, and verify CodeRange's persistent media-storage/serving support.
- [ ] Retry CodeRange port `5001` startup when the unrelated process currently occupying that local port is released by the environment.
