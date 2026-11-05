MAIN := main
TEX  := $(MAIN).tex
SRC  := $(TEX) sections/*.tex refs.bib

all: $(MAIN).pdf

$(MAIN).pdf: $(SRC)
	latexmk -pdf -interaction=nonstopmode -halt-on-error $(TEX)

watch:
	latexmk -pvc -pdf -interaction=nonstopmode $(TEX)

clean:
	latexmk -C

check:
	@echo "— placeholder taraması (TODO kabul edilir, 'placeholder' değil) —"
	@grep -rn -iE "placeholder|Your Paper Title|XXX" . --include='*.tex' || echo "temiz"
	@echo "— çözülmemiş atıf —"
	@grep -iE "undefined (references|citation)" $(MAIN).log || echo "refs OK"
	@echo "— sayfa sayısı —"
	@pdfinfo $(MAIN).pdf 2>/dev/null | grep Pages || true

.PHONY: all watch clean check
