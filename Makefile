test: piep-local.xml
	0launch --command=test piep.xml

piep-local.xml: piep.xml
	0launch http://gfxmonk.net/dist/0install/0local.xml piep.xml

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

0:
	mkzero-gfxmonk -p piep -p setup.py piep.xml

.PHONY: test doc copy clean
