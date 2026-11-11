# User-space host composition. The operating system owns drivers and services.
let
  choices = {
    systems = ["x86_64-linux"];
    formFactors = ["generic" "laptop" "desktop"];
    cpus = ["generic" "intel" "amd"];
    gpus = ["intel-integrated" "intel-discrete" "amd-integrated" "amd-discrete"];
    models = ["generic" "dell-xps-9350"];
  };
  defaults = {
    system = "x86_64-linux";
    formFactor = "generic";
    cpu = "generic";
    gpus = [];
    model = "generic";
    camera = false;
    fingerprint = false;
  };
  fail = message: throw "Invalid Foundation host: ${message}";
  normalize = value: let
    host = defaults // value;
    enum = field: values: builtins.isString host.${field} && builtins.elem host.${field} values;
    validGPUs =
      builtins.isList host.gpus
      && builtins.all (name: builtins.isString name && builtins.elem name choices.gpus) host.gpus
      && builtins.length host.gpus
      == builtins.length (builtins.attrNames (builtins.listToAttrs (map (name: {
          inherit name;
          value = null;
        })
        host.gpus)));
  in
    if !builtins.isAttrs value
    then fail "expected an object"
    else if builtins.any (field: !(builtins.hasAttr field defaults)) (builtins.attrNames value)
    then fail "unknown host field"
    else if !(enum "system" choices.systems && enum "formFactor" choices.formFactors && enum "cpu" choices.cpus && enum "model" choices.models)
    then fail "unsupported system, form factor, CPU or model"
    else if !validGPUs
    then fail "invalid or duplicate GPUs"
    else if !builtins.isBool host.camera || !builtins.isBool host.fingerprint
    then fail "camera and fingerprint must be booleans"
    else if host.model == "dell-xps-9350" && !(host.formFactor == "laptop" && host.cpu == "intel" && builtins.elem "intel-integrated" host.gpus)
    then fail "Dell XPS 9350 requires laptop, Intel CPU and Intel integrated graphics"
    else host // {gpus = builtins.filter (gpu: builtins.elem gpu host.gpus) choices.gpus;};
  fromHardware = hardware:
    if hardware == "dell-xps-9350-intel"
    then
      defaults
      // {
        formFactor = "laptop";
        cpu = "intel";
        gpus = ["intel-integrated"];
        model = "dell-xps-9350";
        camera = true;
      }
    else if hardware == "generic-x86_64"
    then defaults
    else fail "unsupported hardware adapter";
  hardwareFor = host:
    if host.model == "dell-xps-9350"
    then "dell-xps-9350-intel"
    else "generic-x86_64";
in {
  inherit choices defaults normalize fromHardware hardwareFor;
}
