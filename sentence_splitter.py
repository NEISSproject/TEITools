from somajo import SoMaJo

# :: Tokenize German text ::
def SentenceSplit(text):

    tokenizer = SoMaJo("de_CMC")
    tokens = tokenizer.tokenize_text(text)
    return tokens

if __name__ == "__main__":
    string=["Ich teste hiermit, ob Sätze ordentlich getrennt werden können: Ich führe diesen Test am 09. Juli durch. Erhält man mit diesem Tokenizer eine gute Qualität? Wir werden sehen."]
    sentences=SentenceSplit(string)
    for sentence in sentences:
        #print(" ".join([token.text for token in sentence]))
        print(sentence)
