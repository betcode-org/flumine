rm -r build
rm -r dist
rm -r flumine.egg-info

python setup.py sdist bdist_wheel

twine upload dist/*
