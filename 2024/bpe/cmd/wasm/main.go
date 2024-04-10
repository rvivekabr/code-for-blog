package main

import (
	_ "embed"
	"fmt"
	"log"
	"strings"
	"sync"
	"syscall/js"

	"example.com/bpe"
)

//go:embed embed_data/cl100k_base.tiktoken
var vocabFileData string

var vocab map[string]int

func main() {
	var once sync.Once
	once.Do(func() {
		v, err := bpe.LoadTiktokenVocab(strings.NewReader(vocabFileData))
		if err != nil {
			log.Fatal(err)
		}
		vocab = v

		fmt.Printf("vocabulary loaded, len=%v\n", len(vocab))
	})

	js.Global().Set("itsAlive", jsItsAlive)
	js.Global().Set("textToBPETokens", jsTextToBPETokens)

	// For the Go code to be usable from JS, the main function has to run forever.
	<-make(chan bool)
}

var jsItsAlive = js.FuncOf(func(this js.Value, args []js.Value) interface{} {
	result := itsAlive()
	return result
})

func itsAlive() string {
	fmt.Printf("vocabulary loaded, len=%v\n", len(vocab))
	return "go is alive"
}

// textToBPETokens takes text, tokenizes it with BPE using the loaded vocabulary
// and returns the token IDs.
func textToBPETokens(txt string) []int {
	return bpe.Encode(txt, vocab, bpe.CL100KBaseSplitPattern)
}

var jsTextToBPETokens = js.FuncOf(func(this js.Value, args []js.Value) interface{} {
	if len(args) != 1 {
		return "expected 1 argument: text to tokenize"
	}
	txt := args[0].String()
	tokens := textToBPETokens(txt)

	jsTokens := js.Global().Get("Array").New()
	for _, s := range tokens {
		jsTokens.Call("push", js.ValueOf(s))
	}
	return jsTokens
})
