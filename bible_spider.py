import scrapy
import os
from scrapy import Selector
import re 


class BibleSpider(scrapy.Spider):
    name = 'bible'
    start_urls = ['https://www.easyenglish.bible/bible/easy/']

    def parse(self, response):
        #extract the section with the books
        book_section = response.css('.resource-index.biblical').get()
        selector = Selector(text=book_section)
        for i in range(39):  #run on the books, 39 books, Daniel is 26
            if i == 26:
                continue
            book_name = selector.css('h4::text')[i].get().strip()  
                        

            book_directory = os.path.join('output', book_name)
            os.makedirs(book_directory, exist_ok=True)

            
            chapters = selector.css('ul.chapter-list')[i].get()  #extract the chapters of the current book
            chapter_selector = Selector(text=chapters)
            num_of_chapters = len(chapter_selector.css('li a::attr(href)'))
            for j in range(num_of_chapters):
                if j == 0:  #skip the introduction
                    continue
                chapter_link = chapter_selector.css('li a::attr(href)')[j].get()  #run on the chapters of the current book
                chapter_number = chapter_link.split('/')[-2]

                yield scrapy.Request(chapter_link, callback=self.parse_chapter, meta={'book_name': book_name, 'chapter_number': chapter_number})

    def parse_chapter(self, response):
        
        book_name = response.meta['book_name']
        chapter_number = response.meta['chapter_number']

        verses = response.xpath('//p[@sfm="p" or @sfm="m" or @sfm="q1"]//text()').getall()  #extract the verses of the current chapter, it's a list of strings
        chapter_text = ''
        must_copy = False
        for verse in verses:
            if verse in [' "', ' ', '', " '", '.”\u200a', '”\u200a’', '.”\u200a’ ', " '"]:  #skip the non relevant parts   
                continue
            if verse in ['.','. ','.  ', ',',', ', ';', '‘', '.’', '’', '!', '!’', ').', '! ', '?', '? ', ':', ': ']:  #add space after the punctuation
                chapter_text += verse + ' '
                continue
            if must_copy:  #we saw a verse number in the past element, we need to copy the verse
                chapter_text += verse
                must_copy = False
                continue
            if re.search('[a-zA-Z]', verse): #it was a link in the original page, we need to copy it, it's not a new verse
                chapter_text += verse
                continue
            if not re.search('[a-zA-Z]', verse): #it's a verse number
                must_copy = True
                chapter_text += '\n'
                continue
            
        #clean the text     
        chapter_text = chapter_text.replace("   ", " ")
        chapter_text = chapter_text.replace("\xa0", "")
        chapter_text = chapter_text.replace("  ", " ")
        chapter_text = chapter_text.replace("\n", "", 1)
        book_directory = os.path.join('output', book_name)
        os.makedirs(book_directory, exist_ok=True)

        filename = f'output/{book_name}/chapter_{chapter_number}.txt'
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(chapter_text)
        except Exception as e:
            print(f'Error {e} writing file: {filename}')
    
            
