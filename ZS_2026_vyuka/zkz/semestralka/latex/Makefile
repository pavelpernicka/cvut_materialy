.PHONY: all clean
all:
	latexmk -pdf -interaction=nonstopmode -halt-on-error -outdir=build main.tex
	cp build/main.pdf semestralni-prace.pdf
clean:
	latexmk -C -outdir=build main.tex
