test: pup-local.xml
	0launch --command=test2 pup.xml -v

pup-local.xml: pup.xml
	0launch http://gfxmonk.net/dist/0install/0local.xml pup.xml


.PHONY: test
