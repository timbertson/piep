test: piep-local.xml
	0launch --command=test piep-local.xml

piep-local.xml: piep.xml.template
	0launch http://gfxmonk.net/dist/0install/0local.xml piep.xml.template

repl: piep-local.xml
	0launch --command=repl piep-local.xml

doc: piep-local.xml
	0launch --command=doc piep-local.xml -b html -a -E \
		-D version=`cat VERSION` \
		-D release=`cat VERSION` \
		. doc/build

copy: doc
		rsync -avz --delete doc/build/ ~/Sites/gfxmonk/dist/doc/piep/

clean:
	git clean -fdx

.PHONY: test doc copy clean 0 repl
