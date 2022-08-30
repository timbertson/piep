{ lib, python3Packages, nix-update-source }:
let source = nix-update-source.fetch ./src.json; in
with python3Packages;
buildPythonPackage rec {
  inherit (source) src version;
  name = "piep-${version}";
  buildInputs = [ pip ];
  propagatedBuildInputs = [ pygments ];
  checkInputs = [ nose ];
  dontUseSetuptoolsBuild = true;
  dontUsePipInstall = true;
  dontUseSetuptoolsCheck = true;
}
