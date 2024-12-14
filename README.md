# **Project Overview**

The goal of this project was to build a translation model that could translate from modern Hebrew to the Tanach (Hebrew Bible). 
This involved several stages, from data extraction and cleaning to model fine-tuning and generating translations. Below is a step-by-step description of the entire process.
## **Creating the dataset**

### **Learning Scrapy**
   
The first step was to get familiar with [Scrapy](https://scrapy.org/), a powerful Python framework used for web scraping. After learning how to use Scrapy, I utilized it to extract the data needed for the project.

### **Extracting Bible Texts from EasyEnglish.Bible**
   
Using Scrapy, I scraped the [easyenglish.bible](https://www.easyenglish.bible/bible/easy/) christian website, which contains translations of the Bible in modern English.
This step involved extracting all the chapters of each book in the Bible, except for the book of Daniel, as it is written in Aramaic. The extracted chapters were saved as .txt files.
It was crucial to find a site that provided a modern translation of the Bible, as the model was designed to translate from modern Hebrew.
Using older or more formal versions would have made the Hebrew translations less accurate or too formal, so easyenglish.bible was a good fit.
Ideally, I would have preferred to find a modern Hebrew translation of the Tanach, but I couldn't find one, which is why I had to rely on modern English translations for the training data.
Find the entire code of the extraction: [bible_spider.py](bible_spider.py)

### **Cleaning the Extracted Data**
   
After extracting the texts, I needed to clean the files. This involved removing unnecessary elements like links, verse numbers, and any metadata that could interfere with the translation process.
The goal was to make the English-to-Hebrew translation as straightforward as possible.    
In some cases, I removed certain words in the English text, like "and" at the beginning of sentences, because they made the Hebrew translation less modern.
This further refined the dataset for better translation results.
The cleaning is made at the end of the file [bible_spider.py](bible_spider.py).

### **Translating from English to Modern Hebrew**
    
I used the Google Cloud API to translate the English text into modern Hebrew.  
This allowed me to obtain a modern Hebrew translation of the Tanach, which would then be used to train the model to translate from modern Hebrew to biblical Hebrew.
Find the entire code of the traduction from english to hebrew: [traduction.py](traduction.py)

### **Sourcing Original Tanach Verses**
    
For the original Tanach verses, I retrieved data from the [Sefaria](https://www.sefaria.org.il/texts/Tanakh) website. This allowed me to get the Hebrew source text of the Tanach, ensuring the translations were aligned with the original.
Find the entire code: [tanach_api.py](tanach_api.py)

### **Creating the CSV Dataset**
    
I compiled all the data into a CSV file named [dataset](dataset.csv) with two columns: one for the modern Hebrew verses and the other for the corresponding Tanach verses.  
This CSV file became the foundation of the translation model's dataset.

## **Fine-Tuning the Translation Model**
    
For the fine-tuning process, I followed the [Hugging Face NLP Course](https://huggingface.co/learn/nlp-course), specifically the section on [translation tasks](https://huggingface.co/learn/nlp-course/chapter7/4?fw=pt).  
The goal was to fine-tune the [mt5 model](https://huggingface.co/docs/transformers/model_doc/mt5) for our specific task: translating from Hebrew to Tanach.
The entire code is [fine_tuning.ipynb](fine_tuning.ipynb).  
Here we describe some key steps we did in our project:

### Loading Dataset:

In the first step we load our dataset that saved locally.  
```
raw_datasets = load_dataset("csv", data_files="data_test.csv")
```
### Preprocess:

The text is tokenized and truncated to fit within the model's maximum input length.
We load a pre-trained model from Huggingface hub. we chose mt5. 
mT5 is a multilingual extension of Google's T5 (Text-to-Text Transfer Transformer) model, designed to handle a wide range of natural language processing (NLP) tasks across multiple languages (include hebrew).
```
model_checkpoint = 'google/mt5-large'
tokenizer = AutoTokenizer.from_pretrained(model_checkpoint, return_tensors="pt", to_device = device)
model = AutoModelForSeq2SeqLM.from_pretrained(model_checkpoint)
```
Initially, I tried different versions of the mt5 model, but found that the smaller models did not provide satisfactory results.
I opted to use mt5-large because it produced better translations. However, due to hardware limitations, I couldn't use the larger mt5-xl model.
### Training
During training, the model is fine-tuned using the Hugging Face Trainer.  
```
args = Seq2SeqTrainingArguments(
    f"fine_tuned_he_to_tanach",
    evaluation_strategy="no",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8,
    per_device_eval_batch_size=16,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=3,
    predict_with_generate=True,
    fp16=False,
    push_to_hub=True,
)
```
```
trainer = CustomTrainer(
    model,
    args,
    train_dataset=tokenized_datasets['train'],
    eval_dataset=tokenized_datasets['validation'],
    data_collator=data_collator,
    tokenizer=tokenizer,
    compute_metrics=compute_metrics,
)

trainer.train()
```

### **Generating Translations**
    
After the model was trained, I used the generate function from the model to create translations. The following parameters were used to control the output:
```
- min_length=30
- max_length=150
- early_stopping=True
- no_repeat_ngram_size=2
- length_penalty=1.5
```
These parameters helped ensure that the translations were concise, avoided repetition, and were of appropriate length.

### **Push the model**

To push the trained model to Huggingface hub, open push_to_hub.ipynb in Google Colab, upload the model and datasets and run.
we used the command:
```
 trainer.push_to_hub()
```
After training, the model is pushed to the Hugging Face model hub for public use.
[fine_tuned_he_to_tanach](https://huggingface.co/benjaminsul/fine_tuned_he_to_tanach)


## **Inference:**
You can try my model:  
```
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

tokenizer = AutoTokenizer.from_pretrained("benjaminsul/fine_tuned_he_to_tanach")  
model = AutoModelForSeq2SeqLM.from_pretrained("benjaminsul/fine_tuned_he_to_tanach")
text = """what you want in modern hebrew"""

inputs = tokenizer(text, return_tensors='pt', )
summary_ids = model.generate(**inputs, min_length=30,max_length=150, early_stopping=True, no_repeat_ngram_size=2, length_penalty=1.5)
summary = tokenizer.decode(summary_ids[0], skip_special_tokens=True)
print(summary)
```

## **Example outputs:**
I put around 50 example outputs, drawn from short children's stories, in the file [Example_runs](Example_runs), here are some of them
>>> text = דני שמח מאוד והתחיל לטפס על העץ, הוא התקרב לתפוחים וקטף אחד כדי לטעום, הטעם היה מתוק וטעים.  
>>> output = וירד דני על העץ ויקח אחד מן התפוחים ויחמד עליו׃ 


>>>  text: לזכר הניסים הללו אנו מקיימים את חג החנוכה, בו אנו מדליקים חנוכיה ומשחקים בסביבונים  
>>>  output: ויזכרו הנסים האלה אנו מקיימים את חג החנוכה אשר עשה יהוה לנו׃


>>> text =  לדני היה חלום אחד שדרש ממנו המון סבלנות, הוא רצה לגדל עץ תפוחים משלו בחצר האחורית של הבית, דני עשה עבודות אצל הוריו כדי לחסוך כסף לצורך המשימה.  
>>>  output = ויהיה לדני חלום אחד אשר דרש ממנו עבודה רבה ואת עבודתו עשה דני ביד הוריו ותהיה לו תמיד עבדות רבות׃ 


