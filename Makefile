.PHONY: refresh test serve
refresh:
	python run_pipeline.py --refresh
test:
	python -m pytest
serve:
	python -m http.server 8000 --directory web

