{ ... }: {
  xdg.desktopEntries.finite-vates-notes = {
    name = "Vates Notes";
    comment = "Open Vates Notes in Firefox";
    exec = "firefox --new-window https://notes.vates.tech";
    icon = "firefox";
    categories = ["Office"];
  };
}
