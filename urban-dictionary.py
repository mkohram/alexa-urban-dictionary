import logging
from flask import Flask, render_template
from flask_ask import Ask, statement, question, session
import requests

app = Flask(__name__)
ask = Ask(app, '/')
logging.getLogger('flask_ask').setLevel(logging.DEBUG)

URBAN_DICTIONARY_URL = 'http://api.urbandictionary.com/v0/define?term='

@ask.launch
def launch():
    speech_text = 'Welcome to the Urban Dictionary, ask for a definition'
    return question(speech_text).reprompt(speech_text).simple_card('HelloWorld', speech_text)

def find_best(def_list):
    max_thumbs = 0
    choice = None
    for option in def_list:
        if option['thumbs_up'] > max_thumbs:
            max_thumbs = option['thumbs_up']
            choice = option
    return choice

def get_term(term):
    ''' return a json object according to the term given '''
    r = requests.get(URBAN_DICTIONARY_URL+term)
    result = r.json()
    if result['result_type'] == 'no_results':
        return None
    return result

@ask.intent('AskWord', mapping={'term': 'Term'})
def ask_word(term):
    def_dictionary = get_term(term)
    if def_dictionary:
        choice = find_best(def_dictionary['list'])
        definition = choice['definition']
    else:
        text = render_template('not_found')
        return statement(text)

    session.attributes['term'] = term
    session.attributes['term_object'] = choice

    text = render_template('definition', term=term, definition=definition)
    return question(text)

@ask.intent('Example', mapping={'term': 'Term'})
def ask_example(term):
    if term:
        def_dictionary = get_term(term)
        if def_dictionary:
            choice = find_best(def_dictionary['list'])
            example = choice['example']
            session.attributes['term'] = term
            session.attributes['term_object'] = choice
        else:
            text = render_template('not_found')
            return statement(text)
    else:
        try:
            choice = session.attributes['term_object']
            term = session.attributes['term']
            example = choice['example']
        except KeyError:
            text = render_template('not_found')
            return statement(text)

    text = render_template('example', term=term, example=example)
    return question(text)

@ask.intent('AMAZON.StopIntent')
def stop():
    text = render_template('goodbye')
    return statement(text)

@ask.intent('AMAZON.CancelIntent')
def cancel():
    text = render_template('goodbye')
    return statement(text)

@ask.session_ended
def session_ended():
    return "{}", 200

if __name__ == '__main__':
    app.run(debug=True)
