# Home Manager modules

The current layout and dependency conventions are documented in [Feature-owned modules](../MODULES.md). Shared defaults live in `modules/home/base/_home.nix`; applications, roles, capabilities, hosts and providers each own private Home Manager fragments. The [generated graph](../ARCHITECTURE.md) shows the shared Den and CI dependency flow.
