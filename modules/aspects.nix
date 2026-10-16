{den, ...}: {
  den.aspects.features = {
    base.homeManager.imports = [./aspects/base/home.nix];
    capabilities.devops.homeManager.imports = [./aspects/capabilities/devops/home.nix];
    roles = {
      developer = {
        includes = [den.aspects.features.capabilities.devops];
        homeManager.imports = [./aspects/roles/developer/home.nix];
      };
      sales.homeManager.imports = [./aspects/roles/sales/home.nix];
      trainer.homeManager.imports = [./aspects/roles/trainer/home.nix];
      support = {
        includes = [den.aspects.features.capabilities.devops];
        homeManager.imports = [./aspects/roles/support/home.nix];
      };
      executive.homeManager.imports = [./aspects/roles/executive/home.nix];
      it.homeManager.imports = [./aspects/roles/it/home.nix];
    };
    hardware = {
      generic-x86_64.homeManager.imports = [./aspects/hardware/generic-x86_64/home.nix];
      dell-xps-9350-intel.homeManager.imports = [./aspects/hardware/dell-xps-9350-intel/home.nix];
    };
  };
}
