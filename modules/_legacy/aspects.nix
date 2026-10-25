{den, ...}: {
  den.aspects.features = {
    base.homeManager.imports = [./aspects/base/home.nix];
    capabilities.devops.homeManager.imports = [./aspects/capabilities/devops/home.nix];
    profile-composition.homeManager.imports = [./aspects/profile-composition.nix];
    host.homeManager.imports = [./aspects/host.nix];
    machines = {
      generic.homeManager.home.sessionVariables.FINITE_FORM_FACTOR = "generic";
      laptop.homeManager.imports = [./aspects/machines/laptop.nix];
      desktop.homeManager.home.sessionVariables.FINITE_FORM_FACTOR = "desktop";
    };
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
      cpu = {
        generic.homeManager.home.sessionVariables.FINITE_CPU_VENDOR = "generic";
        intel.homeManager.home.sessionVariables.FINITE_CPU_VENDOR = "intel";
        amd.homeManager.home.sessionVariables.FINITE_CPU_VENDOR = "amd";
      };
      gpu = {
        intel-integrated.homeManager.home.sessionVariables.FINITE_GPU_INTEL_INTEGRATED = "1";
        intel-discrete.homeManager.home.sessionVariables.FINITE_GPU_INTEL_DISCRETE = "1";
        amd-integrated.homeManager.home.sessionVariables.FINITE_GPU_AMD_INTEGRATED = "1";
        amd-discrete.homeManager.home.sessionVariables.FINITE_GPU_AMD_DISCRETE = "1";
      };
      models = {
        generic.homeManager = {};
        dell-xps-9350.homeManager.imports = [./aspects/hardware/dell-xps-9350-intel/home.nix];
      };
      generic-x86_64.homeManager.imports = [./aspects/hardware/generic-x86_64/home.nix];
      dell-xps-9350-intel.homeManager.imports = [./aspects/hardware/dell-xps-9350-intel/home.nix];
    };
  };
}
