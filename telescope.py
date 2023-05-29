import matplotlib
matplotlib.use('Agg')
from rtlsdr import RtlSdr
import numpy as np
import matplotlib.pyplot as plt
from astropy import units as u
from astropy.time import Time
from astropy.coordinates import SkyCoord, EarthLocation, AltAz

def observe(center_frequency, bandwidth, n_bins, n_fft, lat, lon, ele, alt, az, save_location='plot.png'):
	
	# initialize SDR
	sdr = RtlSdr()
	sdr.sample_rate = bandwidth
	sdr.center_freq = center_frequency
	sdr.freq_correction = 60
	sdr.gain = 'auto'
	
	# measure spectrum
	psd_sum = np.zeros(n_bins)
	for i in range(n_fft):
		
		samples = sdr.read_samples(n_bins)
		psd = np.abs(np.fft.fft(samples)) ** 2 / (n_bins * bandwidth)
		psd = 10.0 * np.log10(psd)
		
		psd_sum = np.add(psd_sum, np.fft.fftshift(psd))
		
	psd_mean = np.true_divide(psd_sum, n_fft)
	
	sdr.center_freq = center_frequency + 3.2e6
	cal_sum = np.zeros(n_bins)
	for i in range(n_fft):
		
		samples = sdr.read_samples(n_bins)
		cal = np.abs(np.fft.fft(samples)) ** 2 / (n_bins * bandwidth)
		cal = 10.0 * np.log10(cal)
		
		cal_sum = np.add(cal_sum, np.fft.fftshift(cal))
		
	cal_mean = np.true_divide(cal_sum, n_fft)
	
	psd_mean -= cal_mean
	
	# x-axis
	frequency = np.arange(bandwidth / -2.0, bandwidth / 2.0, bandwidth / n_bins)
	frequency += center_frequency
	
	# calculate position in sky
	ra, dec = horizontal_to_equatorial(alt, az, lat, lon, ele)
	
	ra = round(ra, 2)
	dec = round(dec, 2)
	
	# create plot
	plt.plot(frequency, psd_mean)
	plt.title("Spectrum of the the Hydrogen line at RA: " + str(ra) + "deg, Dec: " + str(dec) + "deg")
	plt.xlabel('Frequency (Hz)')
	plt.ylabel('Magnitude (dB)')
	plt.savefig(save_location, bbox_inches='tight')
	
def horizontal_to_equatorial(alt, az, lat, lon, elevation):
	
	loc = EarthLocation(lat=lat*u.deg, lon=lon*u.deg, height=elevation*u.m)
	current_time = Time.now()
	
	altaz = SkyCoord(alt=alt * u.deg, az=az * u.deg, obstime=current_time, frame='altaz', location=loc)
	radec = altaz.icrs
	
	ra = radec.ra.hour
	dec = radec.dec.deg
	
	return (ra, dec)
