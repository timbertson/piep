with (import <nixpkgs> {});
let
	commonDeps = {
		inherit nix-update-source lib;
	};
	makeDev = base: deps:
		let pkg = (import base (commonDeps // deps)); in
		lib.overrideDerivation pkg (base: {
			nativeBuildInputs = base.nativeBuildInputs ++ (
				with pythonPackages; [nose nose_progressive sphinx]
			);
		});
	py2 = makeDev nix/default.nix {
		pythonPackages = python2Packages;
	};
	py3 = makeDev nix/default.nix {
		pythonPackages = python3Packages;
	};
in
lib.addPassthru py2 {
	inherit py2 py3;
}

