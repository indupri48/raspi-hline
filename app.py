from flask import Flask, render_template, request, send_from_directory, redirect
import time
import threading
import sqlite3
import telescope
import os

app = Flask(__name__)

status = 1
states = ['Disconnected', 'Idle', 'Busy']

@app.route('/')
def index():

	qth_file = open('rt.qth', 'r')
	lat = float(qth_file.readline())
	lon = float(qth_file.readline())
	qth_file.close()

	sql = "SELECT * FROM observations"
	connection = sqlite3.connect('rtdb.db')
	connection.row_factory = sqlite3.Row
	observations = connection.execute(sql).fetchall()
	connection.close()

	return render_template('index.html', observations=observations, lat=lat, lon=lon)

@app.route('/submit_request', methods=['POST'])
def submit_request():

	global status

	if status == 2:

		return render_template('response.html', msg='The telescope is busy with another request. Try again later.')

	try:

		# load QTH
		qth_file = open('rt.qth', 'r')
		lat = float(qth_file.readline())
		lon = float(qth_file.readline())
		qth_file.close()

		observation_name = request.form['observation_name']
		observation_name = observation_name.replace(" ", "_")
		center_frequency = float(request.form['center_frequency'])
		bandwidth = float(request.form['bandwidth'])
		n_channels = int(request.form['n_channels'])
		n_bins = int(request.form['n_bins'])
		duration = float(request.form['duration'])

	except:
	
		return render_template('response.html', msg='Bad input. Please check your parameters.')

	x = threading.Thread(target=observe, args=(observation_name, center_frequency, bandwidth, n_channels, n_bins, duration))
	x.start()

	return redirect('/')

@app.route('/delete_observation', methods=['GET'])
def delete_observation():

	observation_id = request.args.get('observation_id')

	sql = "SELECT * FROM observations WHERE id = " + observation_id
	connection = sqlite3.connect('rtdb.db')
	connection.row_factory = sqlite3.Row
	observations = connection.execute(sql).fetchall()
	connection.close()
	
	os.remove('/home/pi/rt/rt_img/' + observations[0]['img_filename'])
	
	sql = "DELETE FROM observations WHERE id = " + observation_id
	connection = sqlite3.connect('rtdb.db')
	cursor = connection.cursor()
	cursor.execute(sql)
	connection.commit()
	connection.close()

	return redirect('/')

@app.route('/update_qth', methods=['POST'])
def update_qth():
	
	lat = request.form['lat']
	lon = request.form['lon']
	
	# checks
	
	qth_file = open('rt.qth', 'w')
	qth_file.write(lat)
	qth_file.write('\n')
	qth_file.write(lon)
	qth_file.close()
	
	return render_template('response.html', msg='Your QTH has been updated succesfully')

@app.route('/status.txt')
def getStatus():

	return "Telescope status: " + states[status]
	
@app.route('/rt_csv/<path:filename>')
def download_csv(filename):
	
	return send_from_directory(directory='/home/pi/rt/rt_csv/', filename=filename)
	
@app.route('/rt_img/<path:filename>')
def download_image(filename):
	
	return send_from_directory(directory='/home/pi/rt/rt_img/', filename=filename)

@app.route('/favicon.ico')
def favicon():

	return send_from_directory(directory='/home/pi/rt/static/', filename='favicon.ico')

def observe(observation_name, center_frequency, bandwidth, n_channels, n_bins, duration):

	global status
	status = 2

	parameters = {
		'dev_args': '',
		'rf_gain': 30,
		'if_gain': 25,
		'bb_gain': 18,
		'frequency': 1420e6,
		'bandwidth': 2.4e6,
		'channels': 2048,
		't_sample': 1,
		'duration': 20,
		'loc': '',
		'ra_dec': '',
		'az_alt': ''
	}

	n_fft = int((duration * bandwidth * 1e6) / float(n_bins))
	print(duration, bandwidth, n_bins, n_fft)

	#virgo.predict(lat=39.8, lon=74.9, source='Cas A', date='2020-12-26')

	#virgo.observe(obs_parameters=parameters, obs_file='observation.dat')

	#virgo.plot(obs_parameters=parameters, n=20, m=35, f_rest=1420e6, vlsr=False, meta=False, avg_ylim=(-5,15), cal_ylim=(-20, 260),obs_file='observation.dat', rfi=[(1419.2e6, 1419.3e6), (1420.8e6, 1420.9e6)], db=True, spectra_csv='spectrum.csv', plot_file='plot.png')

	date_created = int(time.time())

	base_filename = observation_name + "_" + str(date_created)
	csv_filename = base_filename + ".csv"
	img_filename = base_filename + ".png"
		
	telescope.observe(center_frequency * 1e6, bandwidth * 1e6, n_bins, n_fft, 51.0, -1.0, 0.0, 90.0, 0.0, '/home/pi/rt/rt_img/' + img_filename)

	sql = "INSERT INTO observations (observation_name, center_frequency, bandwidth, n_channels, n_bins, duration, date_created, csv_filename, img_filename) VALUES (\'" + observation_name + "\', " + str(center_frequency) + ", " + str(bandwidth) + ", " + str(n_channels) + ", " + str(n_bins) + ", " + str(duration) + ", " + str(date_created) + ", \'" + csv_filename + "\', \'" + img_filename + "\')"
	connection = sqlite3.connect('rtdb.db')
	cursor = connection.cursor()
	cursor.execute(sql)
	connection.commit()
	connection.close()

	status = 1

if __name__ == '__main__':

	app.run(debug=True, host='0.0.0.0')
