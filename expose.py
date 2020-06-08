from Valx_CTgov import extract_values, process_valx_results

def valx_ner(text) : 
	extracted = extract_values(text)
	print(text)
	result = process_valx_results(text, extracted)
	# print("result", result)
	return result


def get_single_response(single_data) : 
	sentence = single_data['sentence'][0]
	valx_result = valx_ner(sentence)
	formatted_response = single_data.copy()
	formatted_response['ner_predictions'] = valx_result
	return formatted_response


def get_response(data) : 
	result_data = [get_single_response(d) for d in data]
	return result_data


