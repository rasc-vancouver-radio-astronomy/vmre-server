set terminal png size 1920,1080
outfile = sprintf("%s.png", filename)
set output outfile
plot filename with lines

