for i in {1..14}
do
	./ting --input-file pair_lists/${i}.csv --output-file ${i}.json
done