NAME = "CCv2"

run:
	python src/CCv2 --verbose

lightmap:
	python src/CCv2 --lightmap

build:
	pyinstaller --onefile --name $(NAME) src/CCv2/__main__.py

clean:
	rm -rf build dist *.spec
