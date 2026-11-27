# Pure descriptor constructor for ordinary Nix applications. Custom recipes stay
# explicit in their features (notably Firefox and Ghostty).
{ name, input, attribute, graphical ? false, pin ? input, recipe ? null, package ? null }: let
  application = {
    inherit input attribute graphical;
    provider = "nix";
    declaration = "nix:${if input == "ai" then pin else input}:${attribute}";
  } // (if pin == input then {} else {inherit pin;})
    // (if recipe == null then {} else {inherit recipe;});
in {
  id = "apps/${name}";
  metadata = { inherit application; } // (if package == null then {} else {package = package // {inherit name;};});
  dependencies = ["providers/${input}"] ++ (if graphical then ["providers/graphics"] else []);
  schemaDependencies = {};
  configuration = _: import ./_application.nix { id = name; inherit application; };
}
