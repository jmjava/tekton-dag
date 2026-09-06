# Build the IEEE draft. IEEEtran is required (TeX Live: texlive-publishers).
MAIN := main
LATEX := pdflatex -interaction=nonstopmode -file-line-error

.PHONY: all pdf bib clean

all: pdf

pdf: $(MAIN).pdf

$(MAIN).pdf: $(MAIN).tex
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

# Optional: if main.tex is converted to \cite + \bibliography{refs}
bib:
	$(LATEX) $(MAIN)
	bibtex $(MAIN)
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

clean:
	rm -f $(MAIN).aux $(MAIN).log $(MAIN).out $(MAIN).bbl $(MAIN).blg $(MAIN).synctex.gz
