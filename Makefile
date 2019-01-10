test: phony
	nosetests --with-doctest --exe

doc: phony
	sphinx-build -b html -a -E \
		-D version=`cat VERSION` \
		-D release=`cat VERSION` \
		. doc/build

copy: doc
	rsync -avz --delete doc/build/ ~/Sites/gfxmonk/dist/doc/piep/

clean: phony
	git clean -fdx

.PHONY: phony
