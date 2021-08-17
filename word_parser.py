# функция поиска слов в предложении
def find(sentence, word_forms):
    import re
    # удаление всех символов из предложения
    sentence = re.sub(r'[^\w\s]', ' ', sentence)
    sentence = sentence.replace('ё', 'е')
    # перебор слов словосочетания
    for type in word_forms:
        flag = False
        # перебор форм слова
        for form in type:
            form = re.sub(r'[^\w\s]', ' ', form)
            if ' ' + form in sentence:
                flag = True
                break
            if form + ' ' in sentence:
                flag = True
                break
            if form == sentence:
                flag = True
                break
        if not flag:
            return False
    return True


# образование списка форм для каждого слова словосочетания
def tagFormsList(tag):
    import pymorphy2
    morph = pymorphy2.MorphAnalyzer()
    tag_words = tag.split()
    forms = []
    for tg in tag_words:
        cur_forms = []
        word = morph.parse(tg)[0]
        cur_forms.append(word.word)
        # word.lexeme - контейнер в котором лежат формы слова (pymorphy2.analyzer.Parse)
        for item in word.lexeme:
            cur_forms.append(item.word)
        forms.append(cur_forms)
    return forms
