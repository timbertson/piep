with (import <nixpkgs> {});
lib.overrideDerivation (callPackage nix/default.nix {}) (base: {
	nativeBuildInputs = base.nativeBuildInputs ++ (
		with python3Packages; [sphinx]
	);
})

