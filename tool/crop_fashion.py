from PIL import Image
import os

img_dir = './results/results_fasion/fasion_PATN_ganppssimperl1_win7/test_660/images'
save_dir = './results/results_fasion/fasion_PATN_ganppssimperl1_win7/test_660/images_crop'

if not os.path.exists(save_dir):
	os.mkdir(save_dir)

cnt = 0

for item in os.listdir(img_dir):
	if not item.endswith('.jpg') and not item.endswith('.png'):
		continue
	cnt = cnt + 1
	print('%d/8570 ...' %(cnt))
	img = Image.open(os.path.join(img_dir, item))
	imgcrop = img.crop((704, 0, 880, 256))
	imgcrop.save(os.path.join(save_dir, item))
