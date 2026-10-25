{
  "id" = "hosts/models/dell-xps-9350";
  "metadata" = {
    "hardware" = {
      "homeManager" = true;
      "imageHardware" = [ "generic-x86_64" ];
      "label" = "Dell XPS 13 9350 (Intel)";
      "name" = "dell-xps-9350-intel";
      "order" = 30;
    };
  };
  "dependencies" = [ ];
  "schemaDependencies" = { };
  configuration = schema: import ./_home.nix;
}
