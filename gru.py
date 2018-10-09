import sys
import numpy as np
import random
import pickle
from pathlib import Path
from keras.callbacks import LambdaCallback
from keras.models import Model
from keras.layers import Input, Embedding, Dense, GRU
from keras.layers import Dropout, multiply, RepeatVector
from keras.optimizers import Adam
from keras.layers.core import Flatten
from keras.layers.wrappers import Bidirectional
from keras.layers.normalization import BatchNormalization


corpus = []
for f in list(Path('lyrics/').glob("**/*.txt")):
    corpus.append(f.read_text().replace(" ", ""))

text = " ".join(corpus)

chars = sorted(list(set(text)))
print('total chars:', len(chars))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))

maxlen = 20
step = 1
sentences = []
next_chars = []
for i in range(0, len(text) - maxlen, step):
    sentences.append(text[i: i + maxlen])
    next_chars.append(text[i + maxlen])
print('nb sequences:', len(sentences))

print('Vectorization...')
x = np.zeros((len(sentences), maxlen), dtype=np.int64)
y = np.zeros((len(sentences), len(chars)), dtype=np.int64)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        x[i, t] = char_indices[char]
    y[i, char_indices[next_chars[i]]] = 1

print('Build model...')

word_input = Input(shape=(maxlen,), dtype=np.int64)
embedded_word = Embedding(input_dim=len(chars)+1, output_dim=512, input_length=maxlen)(word_input)

encoded_word = GRU(256)(embedded_word)
dropout_connection1 = Dropout(rate=0.5)(encoded_word)

attn_input = Dense(1028)(Flatten()(embedded_word))
attn_bn = BatchNormalization()(attn_input)
attn_vec = Dense(256, activation='softmax')(attn_bn)

mul = multiply([dropout_connection1, attn_vec])


decoder_input = RepeatVector(maxlen)(mul)
decoded_word = Bidirectional(GRU(128))(decoder_input)
dropout_connection2 = Dropout(rate=0.5)(decoded_word)
output = Dense(len(chars), activation='softmax')(dropout_connection2)
model = Model(inputs=word_input, outputs=output)

model.compile(loss='categorical_crossentropy', optimizer=Adam())


def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)


def on_epoch_end(epoch, logs):
    # Function invoked at end of each epoch. Prints generated text.
    print()
    print('----- Generating text after Epoch: %d' % epoch)

    start_index = random.randint(0, len(text) - maxlen - 1)
    for diversity in [0.2, 0.5, 1.0, 1.2]:
        print('----- diversity:', diversity)

        generated = ''
        sentence = text[start_index: start_index + maxlen]
        generated += sentence
        print('----- Generating with seed: "' + sentence + '"')
        sys.stdout.write(generated)

        for i in range(100):
            x_pred = np.zeros((1, maxlen))
            for t, char in enumerate(sentence):
                x_pred[0, t] = char_indices[char]

            preds = model.predict(x_pred, verbose=0)[0]
            next_index = sample(preds, diversity)
            next_char = indices_char[next_index]

            generated += next_char
            sentence = sentence[1:] + next_char

            sys.stdout.write(next_char)
            sys.stdout.flush()
        print()


print_callback = LambdaCallback(on_epoch_end=on_epoch_end)

model.fit(x, y,
          batch_size=32,
          epochs=30,
          callbacks=[print_callback])

model.save('encdec_lstm.h5')
