from kba import ask

questions = (
    "Wie heißt du?",
    "Wo wohnst du?",
    "Wie alt bist du?",
    "Was ist dein Lieblingsessen?",
    "Hast du Haustiere?",
    "Ich bin hungrig",
    "Mir ist kalt",
    "Ich habe Durst",
    "Ich bin müde",
    "Ich freue mich",
    "Ich bin traurig",
    "Mir ist langweilig",
    "Ich bin aufgeregt",
    "Ich brauche Hilfe",
    "Ich bin glücklich"
)

answers = tuple(ask(q) for q in questions)

# Print all answers at the end
for i in range(len(questions)):
    print(questions[i])
    print(answers[i])
    print("---------")
