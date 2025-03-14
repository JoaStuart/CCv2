NAME = "CCv2"
EXE = ".venv/bin/python"

run:
	$(EXE) src/CCv2 --verbose

run_proj:
	$(EXE) src/CCv2 --verbose "/home/joa/Documents/Python/CCv2/proj.lpz"

lightmap:
	$(EXE) src/CCv2 --lightmap

build:
	$(EXE) -m pyinstaller --onefile --name $(NAME) src/CCv2/__main__.py

clean:
	rm -rf build dist *.spec/
