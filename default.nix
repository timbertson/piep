with import <nixpkgs> {};
lib.overrideDerivation (
  callPackage nix/default.nix {}
) (o: {
  src = builtins.fetchGit { url = ./.; };
})
