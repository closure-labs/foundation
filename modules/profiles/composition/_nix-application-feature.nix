# Pure descriptor constructor for ordinary Nix applications. Custom recipes stay
# explicit in their features (notably Firefox and Ghostty).
{ name, input, attribute, graphical ? false }: let
  application = {
    inherit input attribute graphical;
    provider = "nix";
    declaration = "nix:${input}:${attribute}";
  };
in {
  id = "apps/${name}";
  metadata = { inherit application; };
  dependencies = ["providers/${input}"] ++ (if graphical then ["providers/graphics"] else []);
  schemaDependencies = {};
  configuration = _: import ./_application.nix { id = name; inherit application; };
}
