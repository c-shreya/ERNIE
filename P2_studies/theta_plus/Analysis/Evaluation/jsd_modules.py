#!/usr/bin/env python3
"""
@author: Shreya Chandrasekharan

This script contains all functions used for text pre-processing and 
for computing Jensen-Shannon Divergence (JSD), Random JSD, and Coherence. 
"""

from textblob import TextBlob, Word
from nltk.util import ngrams
from nltk.probability import FreqDist
from scipy.spatial import distance
from sklearn.feature_extraction.text import CountVectorizer
import sklearn
import numpy as np
import swifter
import pandas as pd
from ast import literal_eval
from scipy import sparse
from sqlalchemy import create_engine

# ------------------------------------------------------------------------------------ #

f = open('stop_words.txt', 'r')
stop_words = [word.rstrip('\n') for word in f]


def preprocess_text(doc, n_grams='one'):
    
    """
    Pre-processing using TextBlob: 
    tokenizing, converting to lower-case, and lemmatization based on POS tagging, 
    removing stop-words, and retaining tokens greater than length 2

    We can also choose to include n_grams (n = 1,2,3) in the final output

    Argument(s): 'doc'        - a string of words or sentences.
                 'n_grams'    - one: only unigrams (tokens consisting of one word each)
                              - two: only bigrams
                              - two_plus: unigrams + bigrams
                              - three: only trigrams 
                              - three_plus: unigrams + bigrams + trigrams

    Output: 'reuslt_singles'  - a list of pre-processed tokens (individual words) of each sentence in 'doc'
            'result_ngrams'   - a list of pre-processed tokens (including n-grams) of each sentence in 'doc'

    """

    blob = TextBlob(doc).lower()
#     lang = blob.detect_language()
#     print(lang)
#     if lang != 'en':
#         blob = blob.translate(to = 'en')

    result_singles = []

    tag_dict = {"J": 'a',  # Adjective
                "N": 'n',  # Noun
                "V": 'v',  # Verb
                "R": 'r'}  # Adverb

    # For all other types of parts of speech (including those not classified at all)
    # the tag_dict object maps to 'None'
    # the method w.lemmatize() defaults to 'Noun' as POS for those classified as 'None'

    for sent in blob.sentences:

        words_and_tags = [(w, tag_dict.get(pos[0])) for w, pos in sent.tags]
        lemmatized_list = [w.lemmatize(tag) for w, tag in words_and_tags]

        for i in range(len(lemmatized_list)):

            if lemmatized_list[i] not in stop_words and len(lemmatized_list[i].lower()) > 2 and not lemmatized_list[i].isdigit():
                result_singles.append(lemmatized_list[i].lower())

    result_bigrams = ['_'.join(x) for x in ngrams(result_singles, 2)]

#     result_bigrams = [
#         token for token in result_bigrams if token != 'psychological_association']

    result_trigrams = ['_'.join(x) for x in ngrams(result_singles, 3)]
    result_two_plus = result_singles + result_bigrams
    result_three_plus = result_singles + result_bigrams + result_trigrams

    if n_grams == 'one':
        result = result_singles
    elif n_grams == 'two':
        result = result_bigrams
    elif n_grams == 'three':
        result = result_trigrams
    elif n_grams == 'two_plus':
        result = result_two_plus
    elif n_grams == 'three_plus':
        result = result_three_plus

    return result


# ------------------------------------------------------------------------------------ #

def get_frequency(processed_text_list):
    
    """
    Using a built-in NLTK function that generates tuples
    We get the frequency distribution of all words/n-grams in a tokenized list
    We can get the proportion of the the token as a fraction of the total corpus size  ----> N/A
    We can also sort these frequencies and proportions in descending order in a dictionary object ----> N/A

    Argument(s): 'processed_text_list' - A list of pre-processed tokens

    Output(s): freq_dict               - A dictionary of tokens and their respective 
                                         frequencies in descending order
    """
    # prop_dict - A dictionary of tokens and their respective proportions as a fraction of the total corpus
    # combined_dict - A dictionary whose values are both frequencies and proportions combined within a list
    # """

    word_frequency = FreqDist(word for word in processed_text_list)

#     sorted_counts = sorted(word_frequency.items(), key = lambda x: x[1], reverse = True)
#     freq_dict = dict(sorted_counts)
    freq_dict = dict(word_frequency)
#     prop_dict = {key : freq_dict[key] * 1.0 / sum(freq_dict.values()) for key, value in freq_dict.items()}
#     combined_dict = {key : [freq_dict[key], freq_dict[key] * 1.0 / sum(freq_dict.values())] for key, value in freq_dict.items()}

    return freq_dict  # , prop_dict, combined_dict


# ------------------------------------------------------------------------------------ #

def merge_vocab_dictionary(vocab_column):
    
    """
    Takes any number of token frequency dictionaries and merges them while summing 
    the respective frequencies and then calculates the proportion of the the tokens 
    as a fraction of the total corpus size and saves to text and CSV files

    Argument(s): vocab_column    - A list/pandas column of dictionary objects

    Output(s): merged_freq_dict  - A list object containing the frequencies of all
                                   merged dictionary tokens 
    """

    merged_freq_dict = {}
    for dictionary in vocab_column:
        for key, value in dictionary.items():  # d.items() in Python 3+
            merged_freq_dict.setdefault(key, []).append(1)

    for key, value in merged_freq_dict.items():
        merged_freq_dict[key] = sum(value)
        
#     # In case we also want proportion of frequency along with counts
#     total_sum = sum(merged_freq_dict.values())
#     merged_prop_dict = {key : merged_freq_dict[key] * 1.0 / total_sum for key, value in merged_freq_dict.items()}
#     merged_combined_dict = {key : [merged_freq_dict[key], (merged_freq_dict[key] * 1.0 / total_sum)] for key, value in merged_freq_dict.items()}

    return merged_freq_dict


# ------------------------------------------------------------------------------------ #

def remove_less_than(frequency_dict, min_threshold = 1):

    """
    Remove any tokens that appear fewer than the min_threshold number of 
    times in a token-frequency dictionary
    
    Argument(s): 'frequency_dict'   - a dictionary of token-frequency pairs
                 'min_threshold'    - Minimum threshold of token frequency to be retained
    
    Output: 'retained'              - a dictionary of all token-frequency pairs after removing
                                      tokens with frequency less than min_threshold
    """
    retained_dict = {key : value for key, value in frequency_dict.items() if (value > min_threshold)}

    return retained_dict

# ------------------------------------------------------------------------------------ #

def filter_after_preprocess(processed_tokens, retained_dict):

    """
    Removes any tokens not in the retained_dict from a list of processed tokens 
    
    Argument(s): processed_tokens  - a list of pre-processed token
                 retained_dict     - a token-frequency dictionary of tokens retained 
                                          after removing tokens up to min_threshold frequency
    
    Output:      filtered          - a list of tokens remaining after filtering out those that
                                     are absent from retained_dict
    """
    filtered = []

    for token in processed_tokens:
        if token in retained_dict.keys():
            filtered.append(token)

    return filtered

# ------------------------------------------------------------------------------------ #

def vectorize(text, corpus_by_cluster, count_vectorizer):
    
    """
    Takes a list and converts it into a vector of document-term probability 
    based on the given corpus
    
    Argument(s): text                - a list of pre-processed tokens
                 corpus_by_cluster   - a list of the corpus tokens
                 count_vectorizer    - scikit-learn's Countvectorizer()
    
    Output:      article_prob_vec    - a list of document-term probabilities
    """

    article_count_mat = count_vectorizer.transform([' '.join(text)])
    article_sum = sparse.diags(1/article_count_mat.sum(axis=1).A.ravel())
    article_prob_vec = (article_sum @ article_count_mat).toarray()

    return article_prob_vec

# ------------------------------------------------------------------------------------ #

def calculate_jsd(doc_prob_vec, cluster_prob_vec):
    
    """
    Computes the Jensen-Shannon Distance (square root of Jensen-Shannon Divergence)
    
    Argument(s): doc_prob_vec       - a list of document-term probabilites
                 cluster_prob_vec   - a list of corpus-term probabilites
    
    Output:      jsd                - Jensen-Shannon Distance between the doc_prob_vec and cluster_prob_vec
    """

    jsd = distance.jensenshannon(doc_prob_vec.tolist()[0], cluster_prob_vec)

    return jsd


# ------------------------------------------------------------------------------------ #


def compute_jsd(data_text, name, val, cluster_num):
    
    """
    Computes the JSD for a cluster dataframe where each row is an article
    
    Argument(s): data_text    - an article cluster dataframe
                 name         - type of edge-weight used 
                                (no-weight, scopus frequency weight, normalized cluster frequency)
                 val          - inflation value used (for MCL)
                 cluster_num  - cluster number to compute JSD for 
    
    Output:      result_dict - a dictionary of JSD output for one cluster     
    """

    original_cluster_size = len(data_text)
    data_text = data_text.dropna()
    final_cluster_size = len(data_text)

    if final_cluster_size < 10:

        result_dict = {
            'weight': name,
            'inflation': val,
            'cluster': cluster_num,
            'total_size': original_cluster_size,
            'pre_jsd_size': final_cluster_size,
            'missing_values': (original_cluster_size-final_cluster_size),
            'post_jsd_size': None,
            'jsd_nans': None,
            'mean_jsd': None,
            'min_jsd': None,
            'percentile_25_jsd': None,
            'median_jsd': None,
            'percentile_75_jsd': None,
            'max_jsd': None,
            'std_dev_jsd': None,
            'total_unique_unigrams': None,
            'final_unique_unigrams':  None,
            'size_1_unigram_prop': None}

    else:

#         data_text['all_text'] = data_text["title"] + " " + data_text["abstract_text"]
#         data_text['processed_all_text'] = data_text["all_text"].swifter.progress_bar(False).apply(preprocess_text)
        
        # If pre-processing is already done:
        data_text['processed_all_text'] = data_text['processed_all_text'].str.split()
        
        data_text['processed_all_text_frequencies'] = data_text['processed_all_text'].swifter.progress_bar(False).apply(get_frequency)
        data_all_text_frequency = merge_vocab_dictionary(data_text['processed_all_text_frequencies'])

        retained_dict = remove_less_than(data_all_text_frequency)
        data_text['filtered_text'] = data_text['processed_all_text'].swifter.progress_bar(False).apply(filter_after_preprocess, args = (retained_dict,))

        mcl_all_text = data_text.filtered_text.tolist()
        corpus_by_article = [' '.join(text) for text in mcl_all_text]
        corpus_by_cluster = [' '.join(corpus_by_article)]

        count_vectorizer = CountVectorizer(lowercase=False, vocabulary=list(set(corpus_by_cluster[0].split())))
        cluster_count_mat = count_vectorizer.fit_transform(corpus_by_cluster)

        data_text['probability_vector'] = data_text['filtered_text'].swifter.progress_bar(False).apply(vectorize, args=(corpus_by_cluster, count_vectorizer,))

        cluster_sum = sparse.diags(1/cluster_count_mat.sum(axis=1).A.ravel())
        cluster_prob_vec = (cluster_sum @ cluster_count_mat).toarray().tolist()[0]

        data_text['JS_distance'] = data_text['probability_vector'].swifter.progress_bar(False).apply(calculate_jsd, args = (cluster_prob_vec,))

        data_text = data_text.dropna()

        data_text['JS_divergence'] = np.square(data_text['JS_distance'])
        jsd_cluster_size = len(data_text)

        jsd_min = min(data_text['JS_divergence'])
        jsd_25_percentile = np.percentile(data_text['JS_divergence'], 25)
        jsd_median = np.percentile(data_text['JS_divergence'], 50)
        jsd_75_percentile = np.percentile(data_text['JS_divergence'], 75)
        jsd_max = max(data_text['JS_divergence'])
        jsd_mean = np.mean(data_text['JS_divergence'])
        jsd_std = np.std(data_text['JS_divergence'])


        result_dict = {
            'weight': name,
            'inflation': val,
            'cluster': cluster_num,
            'total_size': original_cluster_size,
            'pre_jsd_size': final_cluster_size,
            'missing_values': (original_cluster_size-final_cluster_size),
            'post_jsd_size': jsd_cluster_size,
            'jsd_nans': (final_cluster_size-jsd_cluster_size),
            'mean_jsd': jsd_mean,
            'min_jsd': jsd_min,
            'percentile_25_jsd': jsd_25_percentile,
            'median_jsd': jsd_median,
            'percentile_75_jsd': jsd_75_percentile,
            'max_jsd': jsd_max,
            'std_dev_jsd': jsd_std,
            'total_unique_unigrams': len(data_all_text_frequency),
            'final_unique_unigrams': len(retained_dict),
            'size_1_unigram_prop': (1-(len(retained_dict)/len(data_all_text_frequency)))}


    return result_dict


# ------------------------------------------------------------------------------------ #

def random_jsd(jsd_size, sample_data, repeat):
    
    """
    Computes the Random JSD from a randomly sampled set of articles based on a given size
    
    Argument(s): jsd_size     - sample size
                 sample_data  - an article cluster dataframe which was randomly selected
                 repeat       - number of iterations of Random JSD to compute 
    
    Output:      random_jsd   - a list of all iterations of Random JSD values 
    """

    random_jsd = []

    if int(jsd_size) >= 10:

        for i in range(repeat):

            data_text = sample_data.sample(n = int(jsd_size))

#             data_text['all_text'] = data_text["title"] + " " + data_text["abstract_text"]
#             data_text['processed_all_text'] = data_text["all_text"].swifter.progress_bar(False).apply(preprocess_text)

            # If pre-processing is already done:
            data_text['processed_all_text'] = data_text['processed_all_text'].str.split()
            
            data_text['processed_all_text_frequencies'] = data_text['processed_all_text'].swifter.progress_bar(False).apply(get_frequency)

            data_all_text_frequency = merge_vocab_dictionary(data_text['processed_all_text_frequencies'])
            retained_dict = remove_less_than(data_all_text_frequency)
            data_text['filtered_text'] = data_text['processed_all_text'].swifter.progress_bar(False).apply(filter_after_preprocess, args = (retained_dict,))

            data_all_text = data_text.filtered_text.tolist()
            corpus_by_article = [' '.join(text) for text in data_all_text]
            corpus_by_cluster = [' '.join(corpus_by_article)]

            count_vectorizer = CountVectorizer(lowercase=False, vocabulary=list(set(corpus_by_cluster[0].split())))
            cluster_count_mat = count_vectorizer.fit_transform(corpus_by_cluster)

            data_text['probability_vector'] = data_text['filtered_text'].swifter.progress_bar(False).apply(vectorize, args=(corpus_by_cluster, count_vectorizer,))

            cluster_sum = sparse.diags(1/cluster_count_mat.sum(axis=1).A.ravel())
            cluster_prob_vec = (cluster_sum @ cluster_count_mat).toarray().tolist()[0]

            data_text['JS_distance'] = data_text['probability_vector'].swifter.progress_bar(False).apply(calculate_jsd, args = (cluster_prob_vec,))

            data_text = data_text.dropna()
            data_text['JS_divergence'] = np.square(data_text['JS_distance'])

            random_jsd.append(data_text['JS_divergence'].mean())

    else:
        random_jsd = None

    return random_jsd

# ------------------------------------------------------------------------------------ #

# Coherence Functions

def fix_eval_issue(doc):
    """
    Fixes the string literal evalutation issue when reading and writing a
    column of lists to a database table.
    
    Argument(s): doc - a list in a table column
    
    Output:      doc - literal evalutation corrected list
    """
    if doc != 'nan':
        return literal_eval(doc)

    
def compute_mean(row):
    """
    Computes the arithmetic mean of a list using NumPy
    
    Argument(s): row - a list of float values
    
    Output:      mean - arithmetic mean of the list
    """
    if type(row)==list:
        return np.mean(row)

    
def random_jsd_range(row):
    """
    Computes the range of values in a list using NumPy
    
    Argument(s): row   - a list of float values
    
    Output:      range - range of values in the list
    """
    if type(row)==list:
        return np.max(row)-np.min(row)


# ------------------------------------------------------------------------------------ #    
    
schema = "theta_plus"
sql_scheme = 'postgresql://' + "user_name" + ':' + "password" + '@localhost:5432/ernie' # ---> supply credentials
engine = create_engine(sql_scheme)
    
def match_rated_mcl_to_graclus(imm1985_1995_cluster_no, rated_data):
    
    match_year = '19' + str(rated_data.set_index('imm1985_1995_cluster_no').at[int(imm1985_1995_cluster_no), 'match_year'])
    mcl_cluster_no = rated_data.set_index('imm1985_1995_cluster_no').at[int(imm1985_1995_cluster_no), 'match_cluster_no']
    mcl_match_year = 'imm' + match_year + '_cluster_scp_list_unshuffled'
    graclus_match_year = 'imm' + match_year + '_cluster_scp_list_graclus'

    mcl_query = "SELECT * FROM theta_plus." + mcl_match_year + " AS mmy WHERE mmy.cluster_no = " + str(mcl_cluster_no) + ';'
    mcl_data = pd.read_sql(mcl_query, con=engine)
    mcl_cluster_size = len(mcl_data)
    common_nodes = mcl_data['scp'].to_list()
    graclus_query = "SELECT * FROM theta_plus." + graclus_match_year + ';'
    graclus_data = pd.read_sql(graclus_query, con=engine)

    common_graclus_clusters = list(set(graclus_data['cluster_no'][graclus_data['scp'].isin(common_nodes)].to_list()))
    merged_data_intersect = mcl_data[['scp']].merge(graclus_data[graclus_data['cluster_no'].isin(common_graclus_clusters)], how='inner')
    total_in_graclus = len(merged_data_intersect)
    grouped_merged_data_intersect = merged_data_intersect.groupby(by='cluster_no', as_index=False).agg('count')
    max_match_count = grouped_merged_data_intersect['scp'].max()
    
    graclus_cluster_no = grouped_merged_data_intersect.set_index('scp').at[max_match_count, 'cluster_no']
    graclus_cluster_size = len(graclus_data[graclus_data['cluster_no'] == graclus_cluster_no])
    
    graclus_to_mcl_ratio = round(graclus_cluster_size/mcl_cluster_size, 3)
    
    graclus_cluster_query = "SELECT * FROM theta_plus." + graclus_match_year + " AS mmy WHERE mmy.cluster_no = " + str(graclus_cluster_no) + ';'
    graclus_cluster_data = pd.read_sql(graclus_cluster_query, con=engine)
    
    merged_data_union = mcl_data[['scp']].merge(graclus_cluster_data[['scp']], how='outer')
    intersect_check = max_match_count == len(mcl_data[['scp']].merge(graclus_cluster_data[['scp']], how='inner'))
    

    result_dict = {'imm1985_1995_cluster_no': int(imm1985_1995_cluster_no), 
                   'match_year': match_year, 
                   'mcl_cluster_no': mcl_cluster_no, 
                   'mcl_cluster_size': mcl_cluster_size,
                   'graclus_cluster_no': graclus_cluster_no, 
                   'graclus_cluster_size' : graclus_cluster_size,
                   'graclus_to_mcl_ratio': graclus_to_mcl_ratio,
                   'total_in_graclus': total_in_graclus, 
                   'total_intersection': max_match_count,
                   'total_union': len(merged_data_union),
                   'intersect_union_ratio': max_match_count/len(merged_data_union),
                   'intersect_check': intersect_check
                   }
    
    return result_dict



# ------------------------------------------------------------------------------------ #    

def match_superset_year(current_cluster_no, current_year, compare_year, current_year_name, compare_year_name):

        current_cluster_size = len(current_year[current_year["cluster_no"]==current_cluster_no])

        current_grouped = current_year[current_year['cluster_no']==current_cluster_no].merge(compare_year, 
                                                          left_on = 'scp', 
                                                          right_on = 'scp', 
                                                          how='inner')[['cluster_no_y', 'scp']].groupby('cluster_no_y', as_index = False).agg('count')
        current_total_intersection = current_grouped["scp"].sum()
        current_max_count = current_grouped["scp"].max()
        current_max_prop = round(current_max_count/current_cluster_size, 3)

        if (current_total_intersection > 0):#and max_prop >= 0.4:
            compare_cluster_no = current_grouped["cluster_no_y"][current_grouped["scp"] == current_max_count].values[0]
            compare_cluster_size = len(compare_year[compare_year["cluster_no"]==compare_cluster_no])
            compare_max_prop = round(current_max_count/compare_cluster_size, 3)
        else:
            compare_cluster_no = None
            compare_cluster_size = None
            compare_max_prop = None

        current_cluster_number_key = current_year_name + '_cluster_number'
        current_cluster_size_key = current_year_name + '_cluster_size'
        compare_cluster_number_key = compare_year_name + '_cluster_number'
        compare_cluster_prop_key = compare_year_name+ '_max_prop'
        compare_cluster_size_key = compare_year_name+ '_cluster_size'
        compare_to_current_cluster_prop_key = compare_year_name + '_' + current_year_name + '_max_prop'

        match_dict = {
                'current_year': current_year_name,
                current_cluster_number_key: current_cluster_no,
                current_cluster_size_key: current_cluster_size,
                compare_cluster_number_key: compare_cluster_no,
                compare_cluster_size_key: compare_cluster_size,
                compare_cluster_prop_key: current_max_prop,
                compare_to_current_cluster_prop_key: compare_max_prop
                        }

        return match_dict
    
    
# ------------------------------------------------------------------------------------ #    
    
    
def match_mcl_to_graclus(dir_name, cluster_num):
    
    mcl_data_query = "SELECT * FROM theta_plus." + dir_name + "_cluster_scp_list_unshuffled WHERE cluster_no = " + str(cluster_num) + ";"
    mcl_data = pd.read_sql(mcl_data_query, con=engine)
    mcl_cluster_size = len(mcl_data)
    common_nodes = mcl_data['scp'].to_list()
    graclus_query = "SELECT * FROM theta_plus." + dir_name + '_cluster_scp_list_graclus;'
    graclus_data = pd.read_sql(graclus_query, con=engine)

    common_graclus_clusters = list(set(graclus_data['cluster_no'][graclus_data['scp'].isin(common_nodes)].to_list()))
    merged_data_intersect = mcl_data[['scp']].merge(graclus_data[graclus_data['cluster_no'].isin(common_graclus_clusters)], how='inner')

    grouped_merged_data_intersect = merged_data_intersect.groupby(by='cluster_no', as_index=False).agg('count')
    max_match_count = int(grouped_merged_data_intersect['scp'].max())

    graclus_cluster_no = grouped_merged_data_intersect.set_index('scp').at[max_match_count, 'cluster_no']
    if type(graclus_cluster_no) == np.int64:
        graclus_cluster_size = len(graclus_data[graclus_data['cluster_no'] == graclus_cluster_no])
        indicator = 0
    elif type(graclus_cluster_no) == np.ndarray:
        graclus_cluster_no = graclus_cluster_no[0]
        graclus_cluster_size = len(graclus_data[graclus_data['cluster_no'] == graclus_cluster_no])
        indicator = 1

    graclus_to_mcl_ratio = round(graclus_cluster_size/mcl_cluster_size, 3)

    graclus_cluster_query = "SELECT * FROM theta_plus." + dir_name + "_cluster_scp_list_graclus WHERE cluster_no = " + str(graclus_cluster_no) + ";"
    graclus_cluster_data = pd.read_sql(graclus_cluster_query, con=engine)

    merged_data_union = mcl_data[['scp']].merge(graclus_cluster_data[['scp']], how='outer')
        
    result_dict = {'mcl_cluster_no': int(cluster_num), 
                   'mcl_cluster_size': int(mcl_cluster_size),
                   'graclus_cluster_no': int(graclus_cluster_no), 
                   'graclus_cluster_size' : int(graclus_cluster_size),
                   'graclus_to_mcl_ratio': graclus_to_mcl_ratio,
                   'total_intersection': max_match_count,
                   'total_union': len(merged_data_union),
                   'intersect_union_ratio': round(max_match_count/len(merged_data_union), 4),
                   'multiple_options': indicator
                   }

    return result_dict


# ------------------------------------------------------------------------------------ #    
    
    
def match_mcl_to_enriched(dir_name, cluster_num):
    
    mcl_data_query = "SELECT * FROM theta_plus." + dir_name + "_cluster_scp_list_unshuffled WHERE cluster_no = " + str(cluster_num) + ";"
    mcl_data = pd.read_sql(mcl_data_query, con=engine)
    mcl_cluster_size = len(mcl_data)
    common_nodes = mcl_data['scp'].to_list()
    enriched_query = "SELECT * FROM theta_plus." + dir_name + '_enriched_cluster_scp_list_unshuffled;'
    enriched_data = pd.read_sql(enriched_query, con=engine)

    common_enriched_clusters = list(set(enriched_data['cluster_no'][enriched_data['scp'].isin(common_nodes)].to_list()))
    merged_data_intersect = mcl_data[['scp']].merge(enriched_data[enriched_data['cluster_no'].isin(common_enriched_clusters)], how='inner')

    grouped_merged_data_intersect = merged_data_intersect.groupby(by='cluster_no', as_index=False).agg('count')
    max_match_count = int(grouped_merged_data_intersect['scp'].max())

    enriched_cluster_no = grouped_merged_data_intersect.set_index('scp').at[max_match_count, 'cluster_no']
    if type(enriched_cluster_no) == np.int64:
        enriched_cluster_size = len(enriched_data[enriched_data['cluster_no'] == enriched_cluster_no])
        indicator = 0
    elif type(enriched_cluster_no) == np.ndarray:
        enriched_cluster_no = enriched_cluster_no[0]
        enriched_cluster_size = len(enriched_data[enriched_data['cluster_no'] == enriched_cluster_no])
        indicator = 1

    enriched_to_mcl_ratio = round(enriched_cluster_size/mcl_cluster_size, 3)

    enriched_cluster_query = "SELECT * FROM theta_plus." + dir_name + "_enriched_cluster_scp_list_unshuffled WHERE cluster_no = " + str(enriched_cluster_no) + ";"
    enriched_cluster_data = pd.read_sql(enriched_cluster_query, con=engine)

    merged_data_union = mcl_data[['scp']].merge(enriched_cluster_data[['scp']], how='outer')
        
    result_dict = {'mcl_cluster_no': int(cluster_num), 
                   'mcl_cluster_size': int(mcl_cluster_size),
                   'enriched_cluster_no': int(enriched_cluster_no), 
                   'enriched_cluster_size' : int(enriched_cluster_size),
                   'enriched_to_mcl_ratio': enriched_to_mcl_ratio,
                   'total_intersection': max_match_count,
                   'total_union': len(merged_data_union),
                   'intersect_union_ratio': round(max_match_count/len(merged_data_union), 4),
                   'multiple_options': indicator
                   }

    return result_dict