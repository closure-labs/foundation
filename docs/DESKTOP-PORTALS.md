# Restore file dialogs and screen sharing

If Firefox is configured to ask where to save files, it needs a working desktop
file picker. When clicking a download does nothing and no Save As dialog opens,
check the GNOME portal before changing cookies or browser extensions:

```sh
journalctl --user -b -u xdg-desktop-portal-gnome.service --no-pager
journalctl --user -b -u xdg-desktop-portal.service --no-pager
```

An inherited `GDK_BACKEND=wayland,x11` can make the GNOME portal report:

```text
GDK backend forced via env var, portal dialogs will not work properly.
Non-compatible display server, exposing settings only.
```

The service can still appear active while its file chooser and screen-sharing
interfaces are absent. Requests then fail with a missing
`org.freedesktop.impl.portal.FileChooser` interface.

Foundation's Bluefin aspect installs this user-service drop-in:

```text
~/.config/systemd/user/xdg-desktop-portal-gnome.service.d/20-display-backend.conf
```

```ini
[Service]
UnsetEnvironment=GDK_BACKEND
```

The service chooses its backend from the desktop session instead of inheriting
an application override. Foundation does not change applications' environments,
force X11 or Wayland globally, or route all portals through a different backend.
A personal declaration at the same Home Manager path takes precedence over
Foundation's default, so an identical local workaround can be retained or
removed after adopting the containing Foundation revision.

After activating the new generation, restart the portal services when active
screen-sharing sessions can be interrupted:

```sh
systemctl --user daemon-reload
systemctl --user restart xdg-desktop-portal-gnome.service
systemctl --user restart xdg-desktop-portal.service
```

No sudo, browser reset or reboot is required. Retry the browser download and
verify the backend exports its file chooser:

```sh
busctl --user introspect org.freedesktop.impl.portal.desktop.gnome \
  /org/freedesktop/portal/desktop
```

The result should include `org.freedesktop.impl.portal.FileChooser` and
`SaveFile`. Remove global `GDK_BACKEND` declarations from personal configuration
unless a specific application requires one. Scope any necessary override to
that application's launcher. Removing a session variable alone may not clear
copies already inherited by running processes; the service drop-in handles
those stale copies too.

GTK applications support backend fallback lists, but the GNOME portal has its
own display initialization. See the [GTK environment documentation](https://docs.gtk.org/gtk4/running.html)
and [GNOME portal initialization](https://github.com/GNOME/xdg-desktop-portal-gnome/blob/main/src/xdg-desktop-portal-gnome.c).
