function finish_up(button_number)
{
	with(document.abc) {
	
	audio_file_name_hi = "blank";
	transmitter_base_number.value = transmitter_base_number.value;
	text_receiver_number.value = text_receiver_number.value;
	universal_number.value = universal_number.value;
	double_click_speed.value = double_click_speed.value;
	response_duration.value = response_duration.value;
	short_detection_threshold.value = short_detection_threshold.value;
	long_detection_threshold.value = long_detection_threshold.value;
	text_CAU.value = text_CAU.value;
	text_CU1.value = text_CU1.value;
	text_CU2.value = text_CU2.value;
	text_CU3.value = text_CU3.value;
	text_CU4.value = text_CU4.value;	
	text_CU5.value = text_CU5.value;
	text_CU6.value = text_CU6.value;
	text_CU7.value = text_CU7.value;
	text_CU8.value = text_CU8.value;	
	text_CU9.value = text_CU9.value;
	text_CU10.value = text_CU10.value;
	
	min_response_volume.value = minRVout;
	max_response_volume.value = maxRVout;
	min_call_volume.value = minCVout;
	max_call_volume.value = maxCVout;

	switch( button_number ) {
		case 1:
			audio_file_name = "universal_" + short_signal_length.value + "_" + universal_number.value; break;
		case 2:
			if( text_CU1.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU1.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU1.value;
			break;
		case 3:
			if( text_CU2.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU2.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU2.value;
			break;
		case 4:
			if( text_CU3.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU3.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU3.value;
			break;
		case 5:
			if( text_CU4.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU4.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU4.value;
			break;
		case 6:
			if( text_CU5.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU5.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU5.value;
			break;
		case 7:
			if( text_CU6.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU6.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU6.value;
			break;
		case 8:
			if( text_CU7.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU7.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU7.value;
			break;
		case 9:
			if( text_CU8.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU8.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU8.value;
			break;
		case 10:
			if( text_CU9.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU9.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU9.value;
			break;
		case 11:
			if( text_CU10.value < 16 )
				audio_file_name = "unique_" + short_signal_length.value + "_" + text_CU10.value;
			else
				audio_file_name = "unique_" + long_signal_length.value + "_" + text_CU10.value;
			break;
		case 13:
			audio_file_name = "uniq_code_rcv_lo_" + ((text_receiver_number.value * 1) & 0xff);
			if( ((text_receiver_number.value * 1) >> 8) != 0 )
				audio_file_name_hi = "uniq_code_rcv_hi_" + ((text_receiver_number.value * 1) >> 8);
			break;
		case 14:
			audio_file_name = "uniq_code_xmit_base_lo_" + ((transmitter_base_number.value * 1) & 0xff);
			if( ((transmitter_base_number.value * 1) >> 8) != 0 )
				audio_file_name_hi = "uniq_code_xmit_base_hi_" + ((transmitter_base_number.value * 1) >> 8);
			break;
		case 15:
			audio_file_name = "universal_code_" + (universal_number.value * 1); break;
		case 16:
			audio_file_name = "double_click_speed_" + (double_click_speed.value * 1); break;
		case 17:
			audio_file_name = "response_duration_" + (response_duration.value * 1); break;
		case 18:
			audio_file_name = "min_response_volume_" + min_response_volume.value; break;
		case 19:
			audio_file_name = "max_response_volume_" + max_response_volume.value; break;
		case 20:
			audio_file_name = "min_call_volume_" + min_call_volume.value; break;
		case 21:
			audio_file_name = "max_call_volume_" + max_call_volume.value; break;
		case 22:
			audio_file_name = "duration_each_call_vol_" + duration_each_volume.value; break;
		case 23:
			if( flicker_light_yes.checked == true )
				audio_file_name = "flicker_led_1";
			else
				audio_file_name = "flicker_led_0";
			 break;
		case 24:
			if( disable_low_battery_alert_yes.checked == true )
				audio_file_name = "disable_low_battery_1";
			else
				audio_file_name = "disable_low_battery_0";
			 break;
		case 25:
			audio_file_name = "signal_length_short_" + short_signal_length.value; break;
		case 26:
			audio_file_name = "signal_length_long_" + long_signal_length.value; break;
		case 27:
			audio_file_name = "detection_window_size_" + detection_window_size.value; break;
		case 28:
			audio_file_name = "threshold_12_" + (short_detection_threshold.value * 1); break;
		case 29:
			audio_file_name = "threshold_25_" + (long_detection_threshold.value * 1); break;
		case 30:
			text_receiver_number.value = 1;
			select_receiver_number.value = 1;
			transmitter_base_number.value = 0;
			universal_number.value = 1;
			double_click_speed.value = 40;
			response_duration.value = 15;
			min_response_volume.value = 1;
			max_response_volume.value = 4;
			min_call_volume.value = 3;
			max_call_volume.value = 4;
			duration_each_volume.value = 1;
			flicker_light_yes.checked = false;
			flicker_light_no.checked = true;
			disable_low_battery_alert_yes.checked = false;
			disable_low_battery_alert_no.checked = true;
			short_signal_length.value = 5;
			long_signal_length.value = 8;
			detection_window_size.value = 4;
			short_detection_threshold.value = 12;
			long_detection_threshold.value = 32;
			audio_file_name = "factory_reset_0";
			update_call_button(0);
			update_call_button(1);
			break;
	}
	setCookie1();
	audio_file_name = "../keyringer-tones/" + audio_file_name + ".mp3";
	setAndPlayAudioFile();
	if( audio_file_name_hi != "blank" )
	 	waitForAudio();
	}
}