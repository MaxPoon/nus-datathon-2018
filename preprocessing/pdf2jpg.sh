for i in {311..351};
do mkdir -p JPEG/"$i"; for j in `ls $i/*.pdf`;
do convert -density 500 "$j" JPEG/"$j".jpg;
done;
done