def find(sentence, word_forms):
    import re
    sentence = re.sub(r'[^\w\s]', '', sentence)
    sentence = sentence.replace('ё', 'е')
    for type in word_forms:
        flag = False
        for form in type:
            if ' ' + form in sentence:
                flag = True
                break
            if form + ' ' in sentence:
                flag = True
                break
        if not flag:
            return False
    return True


def tagFormsList(tag):
    import pymorphy2
    morph = pymorphy2.MorphAnalyzer()
    tag_words = tag.split()
    forms = []
    for tg in tag_words:
        cur_forms = []
        word = morph.parse(tg)[0]
        cur_forms.append(word.word)
        for item in word.lexeme:
            cur_forms.append(item.word)
        forms.append(cur_forms)
    return forms
