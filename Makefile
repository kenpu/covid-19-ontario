all: ontario

ontario:
	python3 src/download_ontario.py

extract:
	python3 src/extract.py

download:
	mkdir -p wayback_dumps
	python3 src/download_archive.py

serve:
	python -m http.server 8080
