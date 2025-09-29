from enum import Enum
import re
import random
import string
import csv
import os

class text_type(Enum):
    NONE = 1,
    QUESTION = 2,
    STATEMENT = 3

listOfAmounts = [
    "eine", "ein", "zwei", "drei", "vier", "fünf", "sechs", "sieben", "acht", "neun", "zehn",
    "elf", "zwölf", "dreizehn", "vierzehn", "fünfzehn", "sechzehn", "siebzehn", "achtzehn", "neunzehn", "zwanzig",
    "einundzwanzig", "zweiundzwanzig", "dreiundzwanzig", "vierundzwanzig", "fünfundzwanzig",
    "sechsundzwanzig", "siebenundzwanzig", "achtundzwanzig", "neunundzwanzig", "dreißig",
    "viele", "zahlreiche", "unzählige", "mehrere", "einige", "ein paar", "unzählbar",
    "hundert", "tausend", "million", "millionen", "milliarde", "milliarden",
    "unendlich", "keine"
]

def ask(text: str) -> str:
    phrases = split_into_phrases(text)

    for phrase in phrases:
        print(phrase)
        typeOfText = detect_phrase_type(phrase)
        print(typeOfText)

        match typeOfText:
            case text_type.QUESTION:
                return ask_question(phrase)
            case text_type.STATEMENT:
                return ask_statement(phrase)
            case _:
                return ask_blank(phrase)


    return "Sorry hab gerade schlaganfall, aber extrem."
def ask_statement(phrase: str) -> str:
    words = [s.translate(str.maketrans("", "", string.punctuation)) for s in split_into_words(phrase.lower())]
    person = swap_person_context(words[0])
    statement: list[str] = []

    for i in range(len(words)):
        words[i] = swap_person_context(words[i])

    match random.randint(1, 3):
        case 1:
            statement.append("Ich finde auch")
        case 2:
            statement.append("Ich glaube nicht")
        case 3:
            statement.append("Ich bezweifle")
        case _:
            statement.append("Ich find auch")

    statement.append(", dass")
    statement.append(str(person))

    activity = words[1:]
    activity.reverse()
    print(activity[-1][:-1]+"st")

    statement.append(str(" ".join(activity[:-1]) +" "+ activity[-1][:-1]+"st."))

    return build_string_from_array(statement)

def ask_blank(phrase: str) -> str:
    responses = []
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'blank_responses.csv')
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    responses.append(row[0])
    except Exception:
        responses = ["Finde ich auch."]

    if phrase == "ja" or phrase == "nein":
        return "ok"
    elif responses:
        return random.choice(responses)
    else:
        return "Finde ich auch."

def ask_question(phrase: str) -> str:
    words = [s.translate(str.maketrans("", "", string.punctuation)) for s in split_into_words(phrase.lower())]

    statement: list[str] = []

    kannInPhrase = False
    questionTopic = ""

    ####Simple Wie Was questions
    isSimpleWasWieQuestion = check_for_simple_was_wie_question(words)

    #First words kontext
    if words[0] == "kann" or words[0] == "kannst" or words[0] == "können" or words[1] == "kann" or words[1] == "kannst" or words[1] == "können":
        ###Person
        person = swap_person_context(words[2])

        kannInPhrase = True

        #question topic
        questionTopic = " ".join(words[3:])

        match person:
            case "du":
                questionTopic+=" kannst"
            case _:
                questionTopic+=" kann"
    elif words[0] == "hallo":
        words.pop(0)
        p = ask_question(build_string_from_array(words))
        return p
    elif words[1] == "ist":
        person = words[2]
        questionTopic = " ".join(words[3:])+" "+ "e".join(words[1].split("e")[:-1])+ "ist"
    elif words[0] == "ist":
        questionTopic = str(build_string_from_array(words[1:]))+"ist"
        person = "ob"
    elif words[1] == "heißt":
        person = swap_person_context(words[2])
        questionTopic = " ".join(words[3:])+ words[1][:-1]+"e"
    elif words[1] == "braucht" or words[1] == "brauchst":
        person = words[2]
        questionTopic = " ".join(words[3:])+" "+ words[1]
    elif words[0] == "was" or words[0] == "wie" or words[0] == "wieso" or words[0] == "warum" or words[0] == "wer":
        ###Person
        if len(words) > 2:
            person = swap_person_context(words[2])
        else:
            person = "mir"

        #Spezial cases
        if person == "ich" and words[0] == "wer":
            return "Du fragst das noch? Ich bin natürlich der einzig wahre Thorsten, der Drache."
        elif person == "du" and words[0] == "wer":
            return "Du? Das kann ich dir leider noch nicht sagen. Aber ich weis auf jeden fall das du ein Opfer bist."

        match person:
            case "es":
                if words[1] == "geht":
                    if len(words) > 3:
                        questionTopic = swap_person_context(words[3])+" ".join(words[4:])+" "+ "e".join(words[1])
                    elif len(words) > 2:
                        questionTopic = swap_person_context(words[2])+" "+ "e".join(words[1])
                    else:
                        questionTopic = swap_person_context(words[0])+" "+ "e".join(words[1])
                else:
                    questionTopic = " ".join(words[3:])+" "+ "e".join(words[1].split("e")[:-1])+" ist"
            case _:
                if words[3:]:
                    match words[3:][-1]:
                        case "ist":
                            questionTopic = " ".join(words[3:])+" "+ "e".join(words[1].split("e")[:-1])
                        case "so":
                            questionTopic = " ".join(words[3:])+" "+ "e".join(words[1].split("e")[:-1])
                        case _:
                            questionTopic = " ".join(words[3:])+" "+ "e".join(words[1].split("e")[:-1])+"st"
                else:
                    person = " ".join(words[2:])
                    questionTopic = words[1]
        
        if len(words) > 2:
            if words[2] == "bist":
                person = swap_person_context(words[3])
                questionTopic = words[1:-1]
                questionTopic = build_string_from_array([swap_person_context(word) for word in questionTopic])
    else:
        return "Sorry hab gerade schlaganfall."

    ###Building
    if kannInPhrase:
        match random.randint(1, 4):
            case 1:
                statement.append("Als ersters mal, kannst du garnichts, aber wenn du wissen willst")
            case _:
                statement.append("Du willst wissen")
    else:
        statement.append("Du willst wissen")

    if words[0] != "ist":
        statement.append(words[0])
    statement.append(person)

    statement.append(str(questionTopic))

    responses = []
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path = os.path.join(base_dir, 'question_responses.csv')
        
        with open(file_path, newline='', encoding='utf-8') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                if row:
                    responses.append(row[0])
    except Exception:
        responses = [
            ", dann kann ich dir leider nicht helfen.",
            ", dann frage ich mich warum ich das wissen soll.",
            ", dann werde ich dir helfen, indem ich dir ins Gesicht schlage.",
            ", dann solltest du eher mal selbst refelktieren befor du sowas fragst."
        ]

    if responses:
        statement.append(random.choice(responses))
    else:
        statement.append(", dann kann ich dir leider nicht helfen.")


    print("person:",person, "::kann:",kannInPhrase, "::topic", questionTopic, "::simple",isSimpleWasWieQuestion)

    return str(build_string_from_array(statement))

def check_for_simple_was_wie_question(words: list[str]) -> bool:
    print("::"+words[0].lower()+"::")
    if words[0].lower() == "was" or words[0].lower() == "wie":
        return True
    else:
        return False

def detect_phrase_type(phrase: str) -> text_type:
    phrase = phrase.lower()

    ##Basic question checking
    if phrase.count("?") >= 1:
        return text_type.QUESTION

    points: dict[str, int] = {
        'question': 0,
        'statement': 0,
        'blank': 0
    }
    words = split_into_words(phrase)
    for word in words:
        if "was" in word:
            points["question"]+=50
        elif "wie" in word:
            points["question"]+=20
        elif "warum" in word:
            points["question"]+=20
        elif "wieso" in word:
            points["question"]+=20
        elif "wesshalb" in word:
            points["question"]+=20
        elif "wer" in word:
            points["question"]+=20
        elif "ist" in word:
            points["statement"]+=10
        elif "ich" in word:
           points["statement"]+=7
        else:
            points["blank"]+=1
    biggest_var = max(points, key=lambda k: points[k])
    print(points)
    match biggest_var:
        case "question":
            return text_type.QUESTION
        case "statement":
            return text_type.STATEMENT
        case _:
            return text_type.NONE

def split_into_words(text: str):
    return text.split(" ")

def split_into_phrases(text: str):
    # Split by '.', '!', or '?' followed by whitespace or end of string
    phrases = re.split(r'(?<=[.!?])\s+', text)
    # Remove any empty strings
    phrases = [phrase.strip() for phrase in phrases if phrase.strip()]
    return phrases

def build_string_from_array(array: list[str]) -> str:
    string = ""
    for s in array:
        string += s
        string += " "

    return string
def swap_person_context(person: str) -> str:
    match person.lower():
        case "ich":
            return "du"
        case "du":
            return "ich"
        case "mein":
            return "dein"
        case "dein":
            return "mein"
        case "meine":
            return "deine"
        case "deine":
            return "meine"
        case "wir":
            return "ihr"
        case "ihr":
            return "wir"
        case "uns":
            return "euch"
        case "euch":
            return "uns"
        case "mir":
            return "dir"
        case "dir":
            return "mir"
        case "mich":
            return "dich"
        case "dich":
            return "mich"
        case "bist":
            return "bin"
        case "bin":
            return "bist"
        case "habt":
            return "habe"
        case "habe":
            return "habt"
        case "seid":
            return "sind"
        case "sind":
            return "seid"
        case "wird":
            return "werde"
        case "werde":
            return "wird"
        case _:
            return person
