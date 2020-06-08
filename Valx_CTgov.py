# Valx: A system for extracting and structuring numeric lab test comparison statements from text
# Created by Tony HAO, th2510@columbia.edu
# Please kindly cite the paper: Tianyong Hao, Hongfang Liu, Chunhua Weng. Valx: A system for extracting and structuring numeric lab test comparison statements from text. Methods of Information in Medicine. Vol. 55: Issue 3, pp. 266-275, 2016

import W_utility.file as ufile
from W_utility.log import ext_print
import os,sys,re
import Valx_core


fea_dict_dk = ufile.read_csv_as_dict_with_multiple_items('data/variable_features_dk.csv')
fea_dict_umls = ufile.read_csv_as_dict('data/variable_features_umls.csv')
var = 'All'

#load numeric feature list
Valx_core.init_features()

def extract_values(text):
    # read input data
    if text is None or text =="": return False
    # trials = ufile.read_csv (fdin)
    trials = [text]
    if trials is None or len(trials) == 0:
        return False

    # read feature list - domain knowledge
    if fea_dict_dk is None or len(fea_dict_dk) <= 0:
        return False

    # get feature info
    features, feature_dict_dk = {}, {}
    if var == "All":
        features = fea_dict_dk
        if "Variable name" in features : 
            del features["Variable name"]
    elif var in fea_dict_dk:
        features = {var:fea_dict_dk[var]}
    for key, value in fea_dict_dk.items():
        names = value[0].lower().split('|')
        for name in names:
            if name.strip() != '': feature_dict_dk[name.strip()] =key

    # read feature list - UMLS (can be replaced by full UMLS)
    if fea_dict_umls is None or len(fea_dict_umls) <= 0:
        return False 

    output = []
    for i in range(len(trials)):
        # pre-processing eligibility criteria text
        text = Valx_core.preprocessing(trials[i]) # trials[i][1] is the eligibility criteria text
        (sections_num, candidates_num) = Valx_core.extract_candidates_numeric(text) # extract candidates containing numeric features
        for j in range(len(candidates_num)): # for each candidate
            exp_text = Valx_core.formalize_expressions(candidates_num[j]) # identify and formalize values
            (exp_text, key_ngrams) = Valx_core.identify_variable(exp_text, feature_dict_dk, fea_dict_umls) # identify variable mentions and map them to names
            (variables, vars_values) = Valx_core.associate_variable_values(exp_text)
            all_exps = []
            for k in range(len(variables)):
                curr_var = variables[k]
                curr_exps = vars_values[k]
                if curr_var in features:
                    fea_list = features[curr_var]
                    curr_exps = Valx_core.context_validation(curr_exps, fea_list[1], fea_list[2])                           
                    curr_exps = Valx_core.normalization(fea_list[3], curr_exps) # unit conversion and value normalization
                    curr_exps = Valx_core.hr_validation (curr_exps, float(fea_list[4]), float(fea_list[5])) # heuristic rule-based validation
                if len(curr_exps) > 0:
                    if var == "All" or var.lower() == curr_var.lower() or var.lower() in curr_var.lower(): all_exps += curr_exps                     
                 
            if len(all_exps) > 0: output.append((trials[i], sections_num[j], candidates_num[j], exp_text, str(all_exps).replace("u'", "'"))) # output result
    return output



def get_words_space_blocks(text) : 
    """
    Input: text-a string
    Output: [{'word':"word_string", "start":, "end":, "space_length"}....] 
    """
    index=0
    word = ""
    word_space_blocks = [] 
    start_index=0
    end_index=0
    while index<len(text) : 
        character = text[index]
        if character==' ': 
            space_length = 1
            index = index + 1 
            while index < len(text) and character == ' ': 
                character = text[index]
                if character == ' ' : 
                    space_length = space_length + 1 
                    index = index + 1  
            word_space_block = {'word':word, 'start_index':start_index, 'end_index':end_index, 'space_length':space_length}
            word_space_blocks.append(word_space_block)
        else : 
            start_index = index
            index = index + 1 
            while index < len(text) and character != ' ': 
                character = text[index]
                if character != ' ' : 
                    index = index + 1
            end_index = index - 1 
            word = text[start_index:end_index+1]
            if index == len(text) : 
                word_space_block = {'word':word, 'start_index':start_index, 'end_index':end_index, 'space_length':0}
                word_space_blocks.append(word_space_block)

    return word_space_blocks


def get_alphanumeric_groups(word) : 
    """
    Input - 
    Output - 
    """
    all_words = re.findall('[a-zA-Z0-9]+', word)
    return all_words


# def process_valx_results(original_text, valx_output) : 
#     """
#     Input: original_text - The original string passed as input to extract_values function above
#            valx_outputs - The output of extract_values method which is passed the original_text 
#            Let say for text="My weight is 80 kg"
#            valx_output looks like this 
#            [('My weight is 80 kg',
#             'Inclusion',
#             'my weight is 80 kg',
#             'my <VL Label=Weight Source=DK>weight</VL> is <VML Logic=equal Unit=kg>80</VML>',
#             "[['Weight', '=', 80.0, 'kg']]")]


#     Output: Each value detected in valx_output is mapped to its exact starting and ending index in the original string with the type 
#     of value. For eg : 
#             For original_text = My weight is 80 kg, with assuming correct valx_output (i.e weight figured out) 
#             Output = [{'value':"80 kg", "type":"weight", "start_index":13, "end_index":18}]
#     """
#     all_values = valx_output[4]
#     # all_words = original_text.split(" ")
#     # for word in all_words : 

#      # for value in check_value 

def process_valx_results(original_text, valx_outputs) : 

    word_blocks = get_words_space_blocks(original_text)

    all_words = [word_block['word'] for word_block in word_blocks]

    count_word_blocks = len(word_blocks)

    word_block_index = 0

    result = [] 
    
    for output in valx_outputs : 

        value_exps = output[4]
        value_exps = eval(value_exps)

        for value_exp in value_exps :

            value = value_exp[2]
            unit = value_exp[3]
            value_type = value_exp[0]

            float_count = all_words.count(str(value))
            int_count = all_words.count(str(int(value)))
            value_count =  float_count + int_count

            print(value_exp)
            print('value_count', value_count)
            print(word_block_index)
            if len(result)>0 : 
                if result[-1]['entityType'] == value_type and (str(int(value) in get_alphanumeric_groups(result[-1]['entity'])) or str(value) in get_alphanumeric_groups(result[-1]['entity'])) : 
                    continue

            if word_block_index == count_word_blocks : 
                break 

            elif value_count == 1 :
                if float_count == 1 : 
                    word_block_index = all_words.index(str(value))
                else : 
                    word_block_index = all_words.index(str(int(value)))

                if word_block_index <= count_word_blocks - len(unit.split(" ")) - 2 : 
                    word = word_blocks[word_block_index]["word"]
                    word_start_index = word_blocks[word_block_index]['start_index']

                    next_word_blocks = word_blocks[word_block_index+1:word_block_index+len(unit.split(" "))+1]
                    unit_word = " ".join([word_block['word'] for word_block in next_word_blocks])
                    if unit_word == unit : 
                        if len(next_word_blocks) == 0 : 
                            end_index = word_end_index
                        else : 
                            end_index = next_word_blocks[-1]['end_index']
                        result.append({'entity':" ".join([word, unit]), 
                                       "entityType":value_type, 
                                       "startIndex":word_start_index,
                                       "endIndex":end_index, 
                                       "confidence":1})
                        word_block_index = word_block_index + len(unit.split(" ")) + 1 

                    else : 
                        result.append({'entity':word_blocks[word_block_index]['word'], 
                               'entityType':value_type, 
                               'startIndex':word_blocks[word_block_index]['start_index'],
                               'endIndex':word_blocks[word_block_index]['end_index'], 
                               'confidence':1
                              })
                        word_block_index = word_block_index + 1 
                else : 
                    result.append({'entity':word_blocks[word_block_index]['word'], 
                               'entityType':value_type, 
                               'startIndex':word_blocks[word_block_index]['start_index'],
                               'endIndex':word_blocks[word_block_index]['end_index'], 
                               'confidence':1
                              })
                    word_block_index = word_block_index + 1 

            else : 
                while word_block_index < count_word_blocks : 
                    word_block = word_blocks[word_block_index]
                    word = word_block['word']
                    word_start_index = word_block["start_index"]
                    word_end_index = word_block["end_index"]
                    all_alphanumerics = get_alphanumeric_groups(word)

                    if str(value) in all_alphanumerics or str(int(value)) in all_alphanumerics : 
                        if word_block_index <= count_word_blocks - len(unit.split(" ")) - 1 : 
                            next_word_blocks = word_blocks[word_block_index+1:word_block_index+len(unit.split(" "))+1]
                            unit_word = " ".join([word_block['word'] for word_block in next_word_blocks])
                            if unit_word == unit : 
                                if len(next_word_blocks) == 0 : 
                                    end_index = word_end_index
                                else : 
                                    end_index = next_word_blocks[-1]['end_index']
                                result.append({'entity':" ".join([word, unit]), 
                                               "entityType":value_type, 
                                               "startIndex":word_start_index,
                                               "endIndex":end_index, 
                                               "confidence":1
                                               })
                                word_block_index = word_block_index + len(unit.split(" ")) + 1 
                                break 
                    else :
                        if str(value)+unit in all_alphanumerics  or str(int(value))+unit in all_alphanumerics: 
                            result.append({'entity': word, 
                                           'entityType':value_type,
                                           'startIndex':word_start_index,
                                           'endIndex':word_end_index, 
                                           'confidence':1
                                          })
                            word_block_index = word_block_index + 1 
                            break 
                    word_block_index = word_block_index + 1

    return result

        




