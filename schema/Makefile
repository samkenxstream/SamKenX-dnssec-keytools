# http://code.google.com/p/jing-trang/downloads/list
TRANG = java -jar trang.jar

# http://xmlsoft.org/
XMLLINT = xmllint

JAR = trang.jar
RNC = ksr.rnc
RNG = ksr.rng
XSD = ksr.xsd
XML = request.xml response.xml

.SUFFIXES: .rnc .rng .xml .xsd


all: $(JAR) $(RNG) $(XSD)

trang.jar:
	@echo "Download trang.jar from http://code.google.com/p/jing-trang/downloads/list"

.rnc.rng:
	$(TRANG) $< $@

.rnc.xsd:
	$(TRANG) $< $@

validate: $(RNG) $(XML)
	@for i in ${XML}; do \
		${XMLLINT} --noout --relaxng ${RNG} $$i; \
	done

clean:
	rm -f $(RNG) $(XSD)
