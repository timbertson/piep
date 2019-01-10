with (import <nixpkgs> {});
callPackage nix/default.nix { pythonPackages = python3Packages; }
