with (import <nixpkgs> {});
let
	makeDev = base: pythonPackages:
		let pkg = callPackage base { inherit pythonPackages; }; in
		lib.overrideDerivation pkg (base: {
			nativeBuildInputs = base.nativeBuildInputs ++ (
				with pythonPackages; [nose_progressive sphinx]
			);
		});
	py2 = makeDev nix/default.nix python2Packages;
	py3 = makeDev nix/default.nix python3Packages;
in
lib.extendDerivation true {
	inherit py2 py3;
} py3

