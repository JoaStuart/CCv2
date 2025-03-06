NAME = "CCv2"

run:
	python src/CCv2 --verbose

run_proj:
	python src/CCv2 --verbose "C:\Users\Joa\Documents\Python\CCv2\proj.lpz"

lightmap:
	python src/CCv2 --lightmap

build:
	pyinstaller --onefile --name $(NAME) src/CCv2/__main__.py

clean:
	rm -rf build dist *.spec
