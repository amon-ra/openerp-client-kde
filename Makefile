# Makefile for language

UI_FILES:=$(shell find Koo/ui -name "*.ui")
PYTHON_FILES:=$(shell find Koo -name "*.py")
PYTHONC_FILES:=$(shell find Koo -name "*.pyc")
LANGS = ca_ES de_DE es_ES fr hu it pt ro ru sv uk zh al cs el
DIR := Koo/l10n

ALL_MOFILES = ${LANGS:%=${DIR}/%/LC_MESSAGES/koo.mo}
TSFILES = ${LANGS:%=${DIR}/%.ts}

all: mofiles qmfiles
	echo "Message catalogs compiled!"
	

${DIR}/koo.pot: ${PYTHON_FILES}
	# Extract strings with get text from python files
	@xgettext -k_ -kN_ -o $@ $^

mofiles: pofiles ${ALL_MOFILES}

pofiles: ${LANGS:%=${DIR}/%.po}

qmfiles: ${TSFILES} ${LANGS:%=${DIR}/%.qm}

${DIR}/%.po: ${DIR}/koo.pot
	if [ -e $@ ] ; then \
		msgmerge -U $@ $< ;\
	else \
		msginit --no-translator --no-wrap \
			-l $(shell basename $@ .po) -o $@ -i $< ;\
	fi

${DIR}/%/LC_MESSAGES/koo.mo: ${DIR}/%.po
	[ -d $(dir $@) ] || mkdir -p $(dir $@)
	@msgfmt -o $@ $<


# Run lupdate only once and produce all langs
${TSFILES}: ${UI_FILES}
	@pylupdate4 ${UI_FILES} -ts ${TSFILES}

${DIR}/%.qm: ${DIR}/%.ts
	lrelease $< -qm $@

# Merge template with existing translations
# echo "Merging..."
# for x in $LANGS; do
# 	if [ -f $DIR/$x.po ]; then
# 		msgmerge -U $DIR/$x.po $DIR/koo.pot
# 	else
# 		cp $DIR/koo.pot $DIR/$x.po
# 	fi
# 	pylupdate4 $UI_FILES -ts $DIR/$x.ts
# done
# rmdir $DIR/LC_MESSAGES 2>/dev/null
