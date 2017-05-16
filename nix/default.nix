{ lib, pythonPackages, nix-update-source }:
let source = nix-update-source.fetch ./src.json; in
pythonPackages.buildPythonPackage rec {
  inherit (source) src version;
  name = "piep-${version}";
  propagatedBuildInputs = with pythonPackages; [ pygments ];
}
