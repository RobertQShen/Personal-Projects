import pandas as pd
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize, sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.probability import FreqDist
from collections import defaultdict, Counter
import gensim
from gensim import corpora
import matplotlib.pyplot as plt
import os

def preprocess(text):
    """
        Takes the text, checks if it exists, and then tokenizes and stems the words using nltk
    """
    if not isinstance(text, str):
        return []
    
    tokens = word_tokenize(text.lower())
    tokens = [word for word in tokens if word.isalnum() and word not in stop_words and len(word) > 3]
    tokens = [lemmatizer.lemmatize(word) for word in tokens] #compares words to find the stem
    return tokens #list of tokens

def find_dominant_topic(lda, corpus):
    """
        Finds a list of dominant topic words in the lda model
    """
    dominant_topics = []
    for doc in corpus:
        topic_probs = lda_model.get_document_topics(doc) #takes a document in bow format
        dominant_topic = sorted(topic_probs, key=lambda x: x[1], reverse=True)[0][0] #sorts topic probabilities by value then takes the key of the first index
        dominant_topics.append(dominant_topic)
    return dominant_topics

def summarize_paragraph(paragraph, num_sentences):
    """
        Takes a text paragraph and number of sentences we want the summary to be, then ranks the best sentence
    """
    if not isinstance(paragraph, str): #if empty return space
        return ' '
    
    sentences = sent_tokenize(paragraph) #gets list of tokenized sentences
    words = word_tokenize(paragraph.lower()) #gets lsit of tokenized words
    words = [word for word in words if word.isalnum() and word not in stop_words] #filters out stopwords and special characters
    word_frequencies = FreqDist(words)
    sentence_scores = defaultdict(int)
    for sentence in sentences: #counts the number of frequencies the word appears in each sentence
        for word in word_tokenize(sentence.lower()):
            if word in word_frequencies:
                sentence_scores[sentence] += word_frequencies[word]
    sorted_sentences = sorted(sentence_scores, key=sentence_scores.get, reverse=True) #sort sentences by most frequent first
    summary = ' '.join(sorted_sentences[:num_sentences])
    return summary

#Loading the data fro local file path
file_path = os.path.join(os.path.dirname(__file__), "Wiki_Articles.xlsx")
df = pd.read_excel(file_path)
text_data = df['Paragraph'].tolist() #convert Paragraph column to list

#Preprocess the text by dropping stop words and lematizing (stemming)
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('wordnet')
nltk.download('punkt_tab')

lemmatizer = WordNetLemmatizer()
stop_words = set(stopwords.words('english'))

#Train the LDA model on the text
processed_data = [preprocess(doc) for doc in text_data]
dictionary = corpora.Dictionary(processed_data)
corpus = [dictionary.doc2bow(doc) for doc in processed_data]
NUM_TOPICS = 5
lda_model = gensim.models.LdaModel(corpus=corpus,num_topics=NUM_TOPICS,id2word=dictionary,passes=15)

#Get the dominant topics in each document
dominant_topics = find_dominant_topic(lda_model, corpus)
topic_counts = Counter(dominant_topics)

#Get the top topic name from LDA model; you can change how many topic words you want
WORDS=1
topic_names = {i: lda_model.show_topic(i, WORDS) for i in topic_counts.keys()}  #Get top word for topic
topic_labels = {i: f"Topic {i+1}: " + ", ".join([word for word, _ in topic_names[i]]) for i in topic_counts.keys()}

#Map topic IDs to topic names and gets the count for each topic
topics = [topic_labels[i] for i in topic_counts.keys()]
counts = list(topic_counts.values())

#Create a bar chart using matplotlib
plt.figure(figsize=(12, 6))
plt.bar(topics, counts, color='skyblue')
plt.xlabel('Topic')
plt.ylabel('Number of Documents')
plt.title('Distribution of Topics Across Documents')
plt.xticks(rotation=45, ha='right')

#Save the picture
plot_filename = "Topic_Distribution.png"
plt.savefig(plot_filename, bbox_inches="tight", dpi=300)  
plt.close() 

#Summarize each paragraph and add the summary to a new column 'Summary'
df['Summary'] = df['Paragraph'].apply(lambda x: summarize_paragraph(x, 2))

#Save as a new parsed file
df.to_excel('Wiki_Articles_Parsed.xlsx', index=False)



