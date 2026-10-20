# Draft-only A1 data. Production catalogs and writers do not consume this yet.
{catalog}: let
  nix = input: attribute: graphical: {
    provider = "nix";
    inherit input attribute graphical;
    declaration = "nix:${input}:${attribute}";
  };
  flatpak = id: {
    provider = "flatpak";
    remote = "flathub";
    inherit id;
    graphical = true;
    declaration = "flatpak:flathub:${id}";
  };
  launcher = name: {
    provider = "desktop-entry";
    inherit name;
    graphical = false;
    declaration = "desktop-entry:${name}";
  };
  # Keep legacy declarations separately: changing provider is also a migration.
  applications = {
    firefox = nix "nixpkgs-weekly" "firefox" true // {recipe = "configured-firefox";};
    neovim = nix "nixpkgs" "neovim" false;
    bitwarden = nix "nixpkgs-weekly" "bitwarden-desktop" true;
    bitwarden-cli = nix "nixpkgs-weekly" "bitwarden-cli" false;
    element = nix "nixpkgs-weekly" "element-desktop" true;
    libreoffice = nix "nixpkgs-weekly" "libreoffice" true;
    nextcloud = nix "nixpkgs-weekly" "nextcloud-client" true;
    thunderbird = nix "nixpkgs" "thunderbird" true;
    vlc = nix "nixpkgs" "vlc" true;
    marp = nix "nixpkgs" "marp-cli" false;
    ghostty = nix "nixpkgs" "ghostty" true // {recipe = "finite-ghostty";};
    ansible = nix "nixpkgs" "ansible" false;
    openbao = nix "nixpkgs" "openbao" false;
    opentofu = nix "nixpkgs" "opentofu" false;
    packer = nix "nixpkgs" "packer" false;
    devenv = nix "devenv" "devenv" false;
    rustup = nix "nixpkgs" "rustup" false;
    cargo-audit = nix "nixpkgs" "cargo-audit" false;
    cargo-edit = nix "nixpkgs" "cargo-edit" false;
    cargo-watch = nix "nixpkgs" "cargo-watch" false;
    vscodium = nix "nixpkgs" "vscodium" true;
    espanso = nix "nixpkgs" "espanso-wayland" false;
    rustdesk = nix "nixpkgs" "rustdesk-flutter" true;
    damask = flatpak "app.drey.Damask";
    gradia = nix "nixpkgs" "gradia" true;
    pinta = nix "nixpkgs" "pinta" true;
    flatseal = flatpak "com.github.tchx84.Flatseal";
    extension-manager = nix "nixpkgs" "gnome-extension-manager" true;
    distroshelf = nix "nixpkgs" "distroshelf" true;
    camera-controls = nix "nixpkgs" "cameractrls" true;
    ignition = nix "nixpkgs" "ignition" true;
    warehouse = nix "nixpkgs" "warehouse" true;
    icebox = flatpak "io.github.pleromix.IceBox";
    # Nixpkgs.spider is a crawler, not this web-app installer.
    spider = flatpak "io.github.zaedus.spider";
    impression = nix "nixpkgs" "impression" true;
    mission-center = nix "nixpkgs" "mission-center" true;
    gearlever = nix "nixpkgs" "gearlever" true;
    smile = nix "nixpkgs" "smile" true;
    joplin = nix "nixpkgs" "joplin-desktop" true;
    chromium = nix "nixpkgs" "chromium" true;
    refine = nix "nixpkgs" "refine" true;
    rustconn = flatpak "io.github.totoshko88.RustConn";
    grist = launcher "finite-grist";
    vates-notes = launcher "finite-vates-notes";
    hack-font = nix "nixpkgs" "nerd-fonts.hack" false;
    herdr = nix "nixpkgs-unstable" "herdr" false;
    jj = nix "nixpkgs" "jujutsu" false;
    opencode = nix "nixpkgs" "opencode" false;
    uv = nix "nixpkgs" "uv" false;
    gnome-chess = nix "nixpkgs" "gnome-chess" true;
    gnuchess = nix "nixpkgs" "gnuchess" false;
    krita = nix "nixpkgs" "krita" true;
    kdenlive = nix "nixpkgs" "kdePackages.kdenlive" true;
    blender = nix "nixpkgs" "blender" true;
    obs = nix "nixpkgs" "obs-studio" true;
    jellyfin = nix "nixpkgs" "jellyfin-desktop" true;
    audio-player = nix "nixpkgs" "decibels" true;
    steam = nix "nixpkgs" "steam" true;
    heroic = nix "nixpkgs" "heroic" true;
    lutris = nix "nixpkgs" "lutris" true;
  };
  legacyFlatpaks = {
    inherit (applications) damask flatseal icebox spider rustconn;
    gradia = flatpak "be.alexandervanhee.gradia";
    pinta = flatpak "com.github.PintaProject.Pinta";
    extension-manager = flatpak "com.mattjakeman.ExtensionManager";
    distroshelf = flatpak "com.ranfdev.DistroShelf";
    camera-controls = flatpak "hu.irl.cameractrls";
    ignition = flatpak "io.github.flattool.Ignition";
    warehouse = flatpak "io.github.flattool.Warehouse";
    impression = flatpak "io.gitlab.adhami3310.Impression";
    mission-center = flatpak "io.missioncenter.MissionCenter";
    gearlever = flatpak "it.mijorus.gearlever";
    smile = flatpak "it.mijorus.smile";
    joplin = flatpak "net.cozic.joplin_desktop";
    chromium = flatpak "org.chromium.Chromium";
    refine = flatpak "page.tesk.Refine";
  };
  capability = order: label: apps: {
    inherit order label;
    applications = apps;
  };
  devopsApps = ["ghostty" "ansible" "openbao" "opentofu" "packer"];
  developmentApps = ["devenv" "rustup" "cargo-audit" "cargo-edit" "cargo-watch" "vscodium"];
  role = name: defaults: catalog.rolesByName.${name} // {capabilities = defaults;};
  personalRole = name: label: order: defaults: {
    inherit name label order;
    classification = "personal";
    capabilities = defaults;
  };
in {
  schema = 1;
  profileSchema = 3;
  status = "draft";
  inherit applications;
  legacyApplications = applications // legacyFlatpaks;
  roles = {
    developer = role "developer" ["devops" "development"];
    sales = role "sales" ["office" "mail"];
    trainer = role "trainer" ["office" "presentations" "image-editing" "trainer-links"];
    support = role "support" ["devops" "support-tools"];
    executive = role "executive" ["office" "mail" "executive-links"];
    it = role "it" ["remote-desktop"];
    family = personalRole "family" "Family" 110 ["office" "mail"];
    media = personalRole "media" "Media" 120 ["playback"];
    creative = personalRole "creative" "Creative" 130 ["image-editing"];
    gaming = personalRole "gaming" "Gaming" 140 ["casual-games"];
  };
  capabilities = {
    essentials = capability 10 "Browser, credentials and editor" ["firefox" "neovim" "bitwarden" "bitwarden-cli"];
    desktop-tools = capability 20 "Desktop utilities" ["flatseal" "extension-manager" "ignition" "warehouse" "impression" "mission-center" "gearlever" "refine"];
    office = capability 30 "Office documents" ["libreoffice"];
    mail = capability 40 "Mail" ["thunderbird"];
    team-chat = capability 50 "Team chat" ["element"];
    file-sync = capability 60 "File synchronization" ["nextcloud"];
    notes = capability 70 "Notes" ["joplin"];
    playback = capability 80 "Music and video playback" ["vlc"];
    image-editing = capability 90 "Image editing and screenshots" ["pinta" "gradia"];
    presentations = capability 100 "Presentations" ["marp"];
    devops = capability 110 "Development operations" (devopsApps ++ ["distroshelf"]);
    development = capability 120 "Development tools" developmentApps;
    support-tools = capability 130 "Text expansion and remote connections" ["espanso" "rustconn"];
    remote-desktop = capability 140 "Remote desktop" ["rustdesk"];
    trainer-links = capability 150 "Trainer links" ["grist"];
    executive-links = capability 160 "Executive links" ["vates-notes"];
    chromium = capability 170 "Additional Chromium browser" ["chromium"];
    camera-controls = capability 180 "Camera controls" ["camera-controls"];
    web-apps = capability 190 "Web-app installation" ["spider"];
    desktop-comforts = capability 200 "Wallpaper and emoji tools" ["damask" "smile"];
    pdf-tools = capability 210 "PDF and image conversion" ["icebox"];
    casual-games = capability 220 "Chess and engine" ["gnome-chess" "gnuchess"];
    painting = capability 230 "Painting" ["krita"];
    video-editing = capability 240 "Video editing" ["kdenlive"];
    modeling = capability 250 "3D modeling" ["blender"];
    recording = capability 260 "Recording and streaming" ["obs"];
    jellyfin = capability 270 "Jellyfin client" ["jellyfin"];
    audio-player = capability 280 "Focused audio player" ["audio-player"];
    steam = capability 290 "Steam launcher" ["steam"];
    heroic = capability 300 "Heroic launcher" ["heroic"];
    lutris = capability 310 "Lutris launcher" ["lutris"];
  };
  commonCapabilities = ["essentials" "desktop-tools"];
  hardwareCapabilities = {
    generic-x86_64 = [];
    dell-xps-9350-intel = ["camera-controls"];
  };
  optionalPackages = builtins.listToAttrs (map (name: {
      inherit name;
      value = name;
    })
    catalog.packageNames);
  legacy = {
    commonApplications = [
      "firefox"
      "neovim"
      "marp"
      "bitwarden"
      "bitwarden-cli"
      "element"
      "libreoffice"
      "nextcloud"
      "thunderbird"
      "vlc"
      "damask"
      "gradia"
      "pinta"
      "flatseal"
      "extension-manager"
      "distroshelf"
      "camera-controls"
      "ignition"
      "warehouse"
      "icebox"
      "spider"
      "impression"
      "mission-center"
      "gearlever"
      "smile"
      "joplin"
      "chromium"
      "refine"
    ];
    roleApplications = {
      developer = devopsApps ++ developmentApps;
      sales = [];
      trainer = ["grist"];
      support = devopsApps ++ ["espanso" "rustconn"];
      executive = ["vates-notes"];
      it = ["rustdesk"];
    };
  };
  infrastructure = [
    "Foundation commands and transactional activation"
    "Brew provider policy and preflight"
    "Managed Git/Fzf/nh/Zsh integration"
    "Fonts and XDG paths"
    "Generic Linux integration"
    "Role flags and existing role-specific configuration"
    "Dell panel and IPU7/Firefox camera configuration"
  ];
  graphics = {
    preferredBackend = "nixgl-mesa";
    wrapper = "config.lib.nixGL.wrap";
    offload = "explicit-only";
    vulkanDefault = false;
    globalLibraryExports = false;
    legacyBackend = "generic-linux-gpu";
  };
}
