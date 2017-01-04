with (import <nixpkgs> {});
let
	base = import nix/default.nix {
		inherit pythonPackages lib;
		fetchFromGitHub = _ign: ./nix/local.tgz;
	};
in
lib.overrideDerivation base (base: {
	nativeBuildInputs = base.nativeBuildInputs ++ (
		with pythonPackages; [nose nose_progressive sphinx]
	);
})

