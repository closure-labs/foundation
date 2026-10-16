{
  pkgs,
  catalog,
}: let
  profileRuntimeInputs = with pkgs; [coreutils getent gnugrep jq yq-go];
  homeProfile = pkgs.writeShellApplication {
    name = "finite-home-profile";
    runtimeInputs = profileRuntimeInputs;
    text = ''
      foundation=""
      hardware=""
      packages=""
      roles=""
      format=""
      while (( $# > 0 )); do
        case "$1" in
          --foundation) foundation="''${2:?--foundation requires a value}"; shift 2 ;;
          --hardware) hardware="''${2:?--hardware requires a value}"; shift 2 ;;
          --packages) packages="''${2:?--packages requires a value}"; shift 2 ;;
          --roles) roles="''${2:?--roles requires a value}"; shift 2 ;;
          --format) format="''${2:?--format requires a value}"; shift 2 ;;
          *) echo "usage: finite-home-profile --foundation FOUNDATION --hardware HARDWARE --packages PACKAGE,... --roles ROLE,... --format yaml" >&2; exit 2 ;;
        esac
      done
      [[ "$format" == yaml ]] || { echo "--format must be yaml" >&2; exit 2; }
      jq -e --arg foundation "$foundation" --arg hardware "$hardware" '
        .foundations[$foundation].hardware | index($hardware) != null
      ' ${catalog} >/dev/null || {
        echo "Unknown or incompatible foundation/hardware: $foundation/$hardware" >&2
        exit 2
      }

      requested='[]'
      if [[ -n "$roles" ]]; then
        IFS=, read -ra role_list <<<"$roles"
        for role in "''${role_list[@]}"; do
          [[ "$role" =~ ^[a-z][a-z0-9-]*$ ]] || { echo "Invalid role: $role" >&2; exit 2; }
          jq -e --arg role "$role" '.roles[$role]' ${catalog} >/dev/null || {
            echo "Unknown role: $role" >&2
            exit 2
          }
          if jq -e --arg role "$role" 'index($role) != null' <<<"$requested" >/dev/null; then
            echo "Duplicate role: $role" >&2
            exit 2
          fi
          requested=$(jq -c --arg role "$role" '. + [$role]' <<<"$requested")
        done
      fi
      canonical=$(jq -c --argjson requested "$requested" '
        [.roles | to_entries | sort_by(.value.order)[] | .key | select(. as $role | $requested | index($role) != null)]
      ' ${catalog})
      requested_packages='[]'
      if [[ -n "$packages" ]]; then
        IFS=, read -ra package_list <<<"$packages"
        for package in "''${package_list[@]}"; do
          [[ "$package" =~ ^[a-z][a-z0-9-]*$ ]] || { echo "Invalid package: $package" >&2; exit 2; }
          jq -e --arg package "$package" '.packages[$package]' ${catalog} >/dev/null || {
            echo "Unknown package: $package" >&2
            exit 2
          }
          if jq -e --arg package "$package" 'index($package) != null' <<<"$requested_packages" >/dev/null; then
            echo "Duplicate package: $package" >&2
            exit 2
          fi
          requested_packages=$(jq -c --arg package "$package" '. + [$package]' <<<"$requested_packages")
        done
      fi
      canonical_packages=$(jq -c --argjson requested "$requested_packages" '
        [.packages | to_entries | sort_by(.value.order)[] | .key | select(. as $package | $requested | index($package) != null)]
      ' ${catalog})
      username=$(id -un)
      passwd_entry=$(getent passwd "$username")
      home_directory=$(cut -d: -f6 <<<"$passwd_entry")
      [[ "$username" =~ ^[a-z_][a-z0-9_-]*[$]?$ && "$home_directory" == /* ]] || {
        echo "Unable to discover a valid local account identity" >&2
        exit 2
      }

      running="''${FINITE_RUNNING_PROFILE_PATH:-/usr/share/finite/profile.json}"
      if [[ -r "$running" && "''${FINITE_SKIP_FOUNDATION_CHECK:-false}" != true ]]; then
        running_foundation=$(jq -er '.foundation' "$running")
        running_hardware=$(jq -er '.hardware' "$running")
        if [[ "$foundation" != "$running_foundation" ]] ||
          ! jq -e --arg hardware "$hardware" --arg image_hardware "$running_hardware" '
            .hardware[$hardware].imageHardware | index($image_hardware) != null
          ' ${catalog} >/dev/null; then
          echo "Requested $foundation/$hardware is incompatible with running Finite image $running_foundation/$running_hardware" >&2
          exit 2
        fi
      fi

      jq -n \
        --arg foundation "$foundation" \
        --arg hardware "$hardware" \
        --arg username "$username" \
        --arg home "$home_directory" \
        --argjson packages "$canonical_packages" \
        --argjson roles "$canonical" \
        '{schema: 2, foundation: $foundation, hardware: $hardware, packages: $packages, roles: $roles, identity: {username: $username, homeDirectory: $home}}' |
        yq -P
    '';
  };
in
  homeProfile
