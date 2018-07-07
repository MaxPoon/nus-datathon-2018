import pytesseract
from PIL import Image
import os
from concurrent.futures import ProcessPoolExecutor, wait
import pandas as pd
from datetime import datetime


areas = [
	(250, 0, 325, 90),
	(325, 0, 410, 90),
	(415, 0, 485, 90),
	(490, 0, 565, 90),
	(175, 90, 250, 180),
	(250, 90, 325, 180),
	(325, 90, 410, 180),
	(415, 90, 485, 180),
	(490, 90, 565, 180),
	(570, 90, 645, 180),
	(100, 180, 170, 270),
	(175, 180, 250, 270),
	(250, 180, 325, 270),
	(325, 180, 410, 270),
	(415, 180, 485, 270),
	(490, 180, 565, 270),
	(570, 180, 645, 270),
	(650, 180, 735, 270),
	(10, 270, 95, 360),
	(100, 270, 170, 360),
	(175, 270, 250, 360),
	(250, 270, 325, 360),
	(325, 270, 410, 360),
	(415, 270, 485, 360),
	(490, 270, 565, 360),
	(650, 270, 735, 360),
	(10, 365, 95, 450),
	(100, 365, 170, 450),
	(175, 365, 250, 450),
	(250, 365, 325, 450),
	(325, 365, 410, 450),
	(415, 365, 485, 450),
	(490, 365, 565, 450),
	(650, 365, 735, 450),
	(100, 455, 170, 530),
	(175, 455, 250, 530),
	(250, 455, 325, 530),
	(325, 455, 410, 530),
	(415, 455, 485, 530),
	(490, 455, 565, 530),
	(570, 455, 645, 530),
	(650, 455, 735, 530),
	(175, 530, 250, 620),
	(250, 530, 325, 620),
	(325, 530, 410, 620),
	(415, 530, 485, 620),
	(490, 530, 565, 620),
	(570, 530, 645, 620),
	(250, 620, 325, 700),
	(325, 620, 410, 700),
	(415, 620, 485, 700),
	(490, 620, 565, 700)
]


def is_correct_type(img):
	try:
		test_type = int(pytesseract.image_to_string(img.crop((670, 500, 740, 600)), config='-psm 6'))
		return test_type == 24
	except Exception:
		return False


def get_data(img):
	# extract fixation losses
	try:
		cropped_img = img.crop([900, 800, 1100, 900])
		fixation_losses_str = pytesseract.image_to_string(cropped_img, config='-psm 6')
		fixation_losses_str = ''.join([c for c in fixation_losses_str if c.isdigit() or c == '/'])
		fixation_losses = float(eval(fixation_losses_str))
	except Exception:
		fixation_losses = 0

	# extract false pos errors
	try:
		cropped_img = img.crop([920, 900, 1120, 1000])
		false_pos_errors_str = pytesseract.image_to_string(cropped_img, config='-psm 6')
		false_pos_errors_str = ''.join([c for c in false_pos_errors_str if c.isdigit()])
		false_pos_errors = int(false_pos_errors_str)/100
	except Exception:
		false_pos_errors = 0

	# extract false neg errors
	try:
		cropped_img = img.crop([920, 1000, 1120, 1100])
		false_neg_errors_str = pytesseract.image_to_string(cropped_img, config='-psm 6')
		false_neg_errors_str = ''.join([c for c in false_neg_errors_str if c.isdigit()])
		false_neg_errors = int(false_neg_errors_str)/100
	except Exception:
		false_neg_errors = 0

	reliability = (fixation_losses < 0.2) and (false_pos_errors < 0.33) and (false_neg_errors < 0.33)
	return fixation_losses, false_pos_errors, false_neg_errors, reliability


def get_digits(img):
	area = (1850, 2500, 2700, 3200)
	cropped_img = img.crop(area)
	digits = []
	try:
		for area in areas:
			digit = pytesseract.image_to_string(cropped_img.crop(area), config='-psm 6')
			digit = int(digit.strip().replace('O', '0').replace('o', '0').replace("'", '-'))
			digits.append(digit)
		return digits
	except Exception:
		return None


def get_md(img):
	area = (3000, 3100, 3300, 3200)
	try:
		md = pytesseract.image_to_string(img.crop(area), config='-psm 6')
		md = ''.join([c for c in md if c == '-' or c == "'" or c == '.' or c.isdigit()])
		md = float(md)
		return md
	except Exception:
		return None


def get_datetime(datetime_str):
	return datetime(datetime_str[:4], datetime_str[4:6], datetime_str[6:])

def get_data_for_patient(patient_id):
	try:
		file_names = os.listdir('JPEG/'+str(patient_id))
	except FileNotFoundError:
		return None
	# right eyes only
	file_names = [file_name for file_name in file_names if ("OD" in file_name) and ("OS" not in file_name)]
	# sort by dates
	file_names = sorted(file_names, key=lambda file_name: file_name.replace('__', '_').replace('__', '_').split('_')[1])
	data = []
	for file_name in file_names:
		if len(data) == 2:
			break
		file_name_ = file_name.replace('__', '_').replace('__', '_')
		date = file_name_.split('_')[1]
		img = Image.open('JPEG/'+str(patient_id)+'/'+file_name)
		if not is_correct_type(img):
			continue
		fixation_losses, false_pos_errors, false_neg_errors, reliability = get_data(img)
		if not reliability:
			continue
		md = get_md(img)
		if not md:
			continue
		digits = get_digits(img)
		if digits:
			data_dict = {
				'fixation_losses_' + str(len(data) + 1): fixation_losses,
				'false_pos_errors_' + str(len(data) + 1): false_pos_errors,
				'false_neg_errors_' + str(len(data) + 1): false_neg_errors,
				'date_'+str(len(data) + 1): date,
				'md_'+str(len(data) + 1): md
			}
			for j, digit in enumerate(digits):
				data_dict['image_'+str(len(data) + 1)+'_digit_' + str(j + 1)] = digit
			data.append(data_dict)
	if len(data) == 2:
		data_dict = {**data[0], **data[1]}
		data_dict['patient_id'] = patient_id
		data_dict['md_gap'] = data_dict['md_2'] - data_dict['md_1']
		date_1 = get_datetime(data_dict['date_1'])
		date_2 = get_datetime(data_dict['date_2'])
		gap = date_2 - date_1
		data_dict['time_gap'] = gap.days
		data_dict['md_gap_per_year'] = data_dict['md_gap'] / (gap.days / 365)
		return data_dict
	else:
		return None


batch_size = 20
total_num_patients = 136
for i in range(1, total_num_patients+1, batch_size):
	batch_patient_data = []
	for patient_id in range(i, min(i+batch_size, total_num_patients+1)):
		pool = ProcessPoolExecutor(5)
		batch_patient_data.append(pool.submit(get_data_for_patient, patient_id))
	wait(batch_patient_data)
	batch_patient_data = [data.result() for data in batch_patient_data]
	batch_patient_data = [data for data in batch_patient_data if data]
	if i == 1:
		df = pd.DataFrame(columns=batch_patient_data[0].keys())
	start = len(df)
	for j, data in enumerate(batch_patient_data):
		df.loc[start+j] = list(data.values())
	df.to_csv('./patients_data_from_images.csv', index=False)
	print("Processed patient {0} to {1}, {2} of them have reliable data.".format(
		i, min(i+batch_size-1, total_num_patients), len(batch_patient_data)))
