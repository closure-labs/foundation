import ../../profiles/composition/_nix-application-feature.nix {
  name = "chatgpt-desktop";
  input = "ai";
  pin = "chatgpt-desktop";
  attribute = "default";
  graphical = true;
  package = {label = "ChatGPT Desktop"; description = "ChatGPT desktop client for Linux"; order = 90;};
}
