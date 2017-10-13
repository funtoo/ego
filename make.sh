#!/bin/bash

VERSION=`cat VERSION`

prep() {
	install -d dist
	rm -f dist/ego-$VERSION*
	cd doc
	for x in *.rst; do
	    cat $x | sed -e "s/##VERSION##/$VERSION/g" | rst2man.py > ${x%.rst}
    done
	cd ..
	sed -i -e '/^VERSION =/s/^.*$/VERSION = "'$VERSION'"/g' ego
}

commit() {
	cd doc
	git add *.[1-8]
	cd ..
	git commit -a -m "$VERSION distribution release"
	git tag -f "$VERSION"
	git push
	git push --tags
	git archive --format=tar --prefix=ego-${VERSION}/ HEAD > dist/ego-${VERSION}.tar
	bzip2 dist/ego-$VERSION.tar
}


if [ "$1" = "prep" ]
then
	prep
elif [ "$1" = "commit" ]
then
	commit
elif [ "$1" = "all" ]
then
	prep
	commit
fi
