ZIP=zip

all: zip 

report:
	pdflatex report.tex

zip: report
	$(ZIP) 07-brute.zip decide.py report.pdf
