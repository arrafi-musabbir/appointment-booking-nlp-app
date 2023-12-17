from flask import Flask, request, jsonify
import spacy
import json
import datefinder
import re
from datetime import datetime, timedelta
import pandas as pd
nlp = spacy.load("en_core_web_lg")

def classifyText(text):
    doc = nlp(text)
    results = {}

    # extracting intent
    appointment = ['set', 'book', 'make', 'create', 'arrage', 'assign', 'schedule']
    reschedule = ['reschedule', 'move', 'postpone', 'delay', 'defer', 'rearrange']
    cancel = ['cancel', 'revoke', 'abort', 'withdraw', 'discard']
    list_apmts = ['see', 'show', 'list', 'record']
    for i in text.split():
        if i.strip().lower() in appointment:
            results['intent'] = 'make appointment'
            intent = 1
            break
        elif i.strip().lower() in reschedule:
            results['intent'] = 'reschedule appointment'
            intent = 2
            break
        elif i.strip().lower() in cancel:
            results['intent'] = 'cancel appointment'
            intent = 3
            break
        elif i.strip().lower() in list_apmts:
            results['intent'] = 'list appointment'
            intent = 4
            break

    verbs = ['regarding', 'concerning']
    # extracting name and topic
    topic = []
    person = []
    for token in doc:
        # Try this with other parts of speech for different subtrees.
        if token.pos_ == 'ADP':
            if token.text == 'with':
                person.append(' '.join([tok.orth_ for tok in token.subtree]).replace('with', ''))
            if token.text == 'about':
                topic.append(' '.join([tok.orth_ for tok in token.subtree]))
        if token.pos_ == 'VERB':
            if token.text in verbs:
                topic.append(' '.join([tok.orth_ for tok in token.subtree]))

    if len(topic) > 0:
        if len(person) > 0:
            person = person[0].replace(topic[0], '')
            results['person'] = [i.strip() for i in person.split('and')]

        results['topic'] = [i.replace('about', '').strip() for i in topic[0].split('and')]
        for v in verbs:
            results['topic'] = [i.replace(v, '').strip() for i in results['topic'][0].split('and')]

    elif len(person) > 0:
        results['person'] = [i.strip() for i in re.split(r', | and ',   person[0])]

    results['person'] = [i.split(',') for i in results['person']]
    results['person'] = [item.strip() for sublist in results['person'] for item in sublist]
    
    days = ['today', 'tomorrow', 'yesterday', 'this week', 'next week', 'day after tomorrow']
    day_s = ''
    count = 0
    for day in days:
        if text.find(day) != -1:
            if count > 1:
                break
            # Extract and parse the explicit dates and date keywords
            explicit_dates = parse_explicit_dates(text)
            date_keywords_dates = parse_date_keywords(text)

            # Combine the parsed dates
            parsed_dates =  date_keywords_dates + explicit_dates
            # Print the extracted dates
            if parsed_dates:
                day_s = day
                for i, date in enumerate(parsed_dates):
                    print(f"Date {i + 1}: {date.strftime('%d-%m-%Y')}")
                    results['date{}'.format(count)] = date.strftime('%d-%m-%Y')
                    results['time{}'.format(count)] = date.strftime('%H:%M')
                    count = count + 1

                    if intent == 3 or intent == 4:
                        # print(intent)
                        if day == 'this week' or day == 'next week':
                            results['date{}'.format(count)] = (date + timedelta(days=6)).strftime('%d-%m-%Y')
                            results['time{}'.format(count)] = date.strftime('%H:%M')

            else:
                print("No dates found.")

    # print(count)

    # extracting date and time
    matches = list(datefinder.find_dates(text))
    # print(matches)

    if count < 1:
        print('match count<1')
        for match in matches:
            print(match)
            results['date{}'.format(count)] = match.strftime('%d-%m-%Y')
            results['time{}'.format(count)] = match.strftime('%H:%M')
            count = count + 1
    elif count < 2:
        print('match count<2')

        if day_s == 'tomorrow':
            print(matches)
            if len(matches) > 1:
                a, b = matches
                # print("here", a, v)
                results['date{}'.format(count)] = b.strftime('%d-%m-%Y')
                results['time{}'.format(count)] = b.strftime('%H:%M')
                results['time{}'.format(count-1)] = a.strftime('%H:%M')
                count = count + 1
            elif len(matches) == 1:
                results['time{}'.format(count-1)] = matches[count-1].strftime('%H:%M')
                # results['datetime']['time{}'.format(count)] = b.strftime('%H:%M')
                # results['datetime']['time{}'.format(count-1)] = a.strftime('%H:%M')
                # count = count + 1
    elif count == 2:
        print('match count==2')
        if len(matches) > 1:
            for i in range(count):
                results['time{}'.format(i)] = matches[i].strftime('%H:%M')
        elif len(matches) == 1:
            for match in matches:
                # print(match)
                results['time{}'.format(count-1)] = match.strftime('%H:%M')

    json_object = json.dumps(results, indent = 4)
    return json_object

# Function to parse explicit dates
def parse_explicit_dates(sentence):
    # List of days of the week starting from Monday
    days_of_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']

    # Find matches for days of the week in the sentence
    date_matches = re.findall(r'\b(?:' + '|'.join(days_of_week) + r')\b', sentence, flags=re.IGNORECASE)

    # Get today's date as a starting point
    current_date = datetime.now()

    # Calculate the date for the specified day of the week
    parsed_dates = []
    for day_match in date_matches:
        day_match = day_match.lower()
        days_until_target = (days_of_week.index(day_match) - current_date.weekday() + 7) % 7
        target_date = current_date + timedelta(days=days_until_target)
        parsed_dates.append(target_date)

    return parsed_dates

# Function to parse date keywords
def parse_date_keywords(sentence):
    date_keywords = {
        'yesterday': timedelta(days=-1),
        'today': timedelta(days=0),
        'tomorrow': timedelta(days=1),
        'day after tomorrow': timedelta(days=2),
        'last week': timedelta(weeks=-1),
        'this week': timedelta(weeks=0),
        'next week': timedelta(weeks=1)
    }

    # Find matches for date keywords in the sentence
    date_matches = re.findall(r'\b(?:' + '|'.join(date_keywords.keys()) + r')\b', sentence, flags=re.IGNORECASE)

    # Get today's date as a starting point
    current_date = datetime.now()

    # Calculate the date for the specified date keywords
    parsed_dates = [current_date + date_keywords[key.lower()] for key in date_matches]

    return parsed_dates

if __name__ == '__main__':
    print(classifyText('I want to set a meeting with Ayon on Monday at 3 pm'))