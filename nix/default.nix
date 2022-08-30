{ lib, python3Packages }:
with python3Packages;
let version = builtins.readFile ../VERSION; in
buildPythonPackage rec {
  src = ../.;
  name = "piep-${version}";
  propagatedBuildInputs = [ pygments ];
  checkInputs = [ nose ];
}
