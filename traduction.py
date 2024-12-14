from google.cloud import translate_v2 as translate
import os
import pandas as pd
import tanach_api
import re
import html


os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "C:/Users/sulta/OneDrive/Bureau/technion/semestre_9/project/translate_key.json"

def translate_text(english_text, target_language='he'):
    client = translate.Client()
    result = client.translate(english_text, target_language=target_language)

    translated_text = result['translatedText']
    return translated_text




books = tanach_api.get_tanakh_books()
books.remove('Daniel')
data_en = []
data_no_en = []

df = pd.DataFrame(columns=['he', 'tanach'])

for book in books:
    
    num_of_chapters = tanach_api.get_num_of_chapters(book)
    for chapter in range(1, num_of_chapters + 1):
        if book == 'Joel' and chapter == 4:
            continue
        print(f"Translating {book} chapter {chapter}")
        path_en = f"C:/Users/sulta/OneDrive/Bureau/technion/semestre_9/project/bible_scraper/output/{book}/chapter_{chapter}.txt"
        path_ta = f"C:/Users/sulta/OneDrive/Bureau/technion/semestre_9/project/tanah/{book}/chapter_{chapter}.txt"
        with open(path_en, 'r', encoding='utf-8') as file_en, open(path_ta, 'r', encoding= "utf-8-sig") as file_ta:
            versets_en = file_en.readlines()
            psukim = file_ta.readlines()
            if len(versets_en) != len(psukim):
                continue
                
        i = 0
        for verset,pasuk in zip(versets_en,psukim):
            
            
            print("verset: ", i)
            i += 1
            hebrew_version = translate_text(verset, target_language='he')
            hebrew_version = html.unescape(hebrew_version)
            hebrew_version = re.sub(r'<.*?>', '', hebrew_version)  # remove html entities
            hebrew_version = re.sub(r'&#39;', '', hebrew_version) 
               
            data_no_en.clear()
            data_no_en.append ({'he': hebrew_version.strip() , 'tanach': pasuk.strip()})
            df = pd.concat([df, pd.DataFrame(data_no_en)], ignore_index=True)
            df.to_csv('C:/Users/sulta/OneDrive/Bureau/technion/semestre_9/project/data_no_en.csv', index=False, encoding='utf-8-sig')
            


