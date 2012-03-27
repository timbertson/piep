test: piep-local.xml
	0launch --command=test piep.xml -v

piep-local.xml: piep.xml
	0launch http://gfxmonk.net/dist/0install/0local.xml piep.xml


.PHONY: test
