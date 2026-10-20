let
  classifications = [
    {
      name = "professional";
      label = "Professional";
      order = 10;
    }
    {
      name = "personal";
      label = "Personal";
      order = 20;
    }
  ];
  foundations = [
    {
      name = "bluefin";
      label = "Bluefin";
      order = 10;
      template = "home-bluefin";
    }
    {
      name = "bluefin-dx";
      label = "Bluefin DX";
      order = 20;
      template = "home-bluefin-dx";
    }
  ];
  hardware = [
    {
      name = "generic-x86_64";
      label = "Generic x86-64";
      order = 10;
      homeManager = true;
      imageHardware = ["generic-x86_64"];
    }
    {
      name = "dell-xps-9350-intel";
      label = "Dell XPS 13 9350 (Intel)";
      order = 30;
      homeManager = true;
      imageHardware = ["generic-x86_64"];
    }
  ];
  roles = [
    {
      name = "developer";
      label = "Developer";
      classification = "professional";
      order = 10;
      homeCompatible = false;
    }
    {
      name = "sales";
      label = "Sales";
      classification = "professional";
      order = 20;
      homeCompatible = true;
    }
    {
      name = "trainer";
      label = "Trainer";
      classification = "professional";
      order = 30;
      homeCompatible = true;
    }
    {
      name = "support";
      label = "Support";
      classification = "professional";
      order = 40;
      homeCompatible = true;
    }
    {
      name = "executive";
      label = "Executive";
      classification = "professional";
      order = 50;
      homeCompatible = false;
    }
    {
      name = "it";
      label = "IT";
      classification = "professional";
      order = 60;
      homeCompatible = false;
    }
  ];
  packages = [
    {
      name = "hack-font";
      label = "Hack Nerd Font";
      description = "Hack font patched with Nerd Fonts glyphs";
      order = 10;
    }
    {
      name = "herdr";
      label = "Herdr";
      description = "Terminal process manager";
      order = 20;
    }
    {
      name = "jj";
      label = "Jujutsu";
      description = "Jujutsu version-control system (jj)";
      order = 30;
    }
    {
      name = "opencode";
      label = "OpenCode";
      description = "Open-source coding agent";
      order = 40;
    }
    {
      name = "uv";
      label = "uv";
      description = "Python package and project manager";
      order = 50;
    }
  ];
  names = entries: map (entry: entry.name) entries;
  toAttrs = entries:
    builtins.listToAttrs (
      map (entry: {
        inherit (entry) name;
        value = entry;
      })
      entries
    );
  homeHardware = builtins.filter (entry: entry.homeManager) hardware;
in {
  inherit classifications foundations hardware packages roles;
  classificationsByName = toAttrs classifications;
  foundationsByName = toAttrs foundations;
  hardwareByName = toAttrs hardware;
  packagesByName = toAttrs packages;
  rolesByName = toAttrs roles;
  classificationNames = names classifications;
  foundationNames = names foundations;
  templateNames = map (foundation: foundation.template) foundations;
  homeHardwareNames = names homeHardware;
  packageNames = names packages;
  roleNames = names roles;
  homeCompatibleRoleNames = names (builtins.filter (role: role.homeCompatible) roles);
}
