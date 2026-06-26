import { useState, useEffect, useRef } from "react";
import axios from "axios";

const API_URL = "http://localhost:8000";

export default function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [deck, setDeck] = useState([]);
  const [inkSaver, setInkSaver] = useState(false);
  const [addSpace, setAddSpace] = useState(false);
  const debounceTimer = useRef(null);

  // Search with 200ms debounce
  useEffect(() => {
    if (debounceTimer.current) clearTimeout(debounceTimer.current);
    debounceTimer.current = setTimeout(async () => {
      if (query.trim() === "") {
        setResults([]);
        return;
      }
      const res = await axios.get(`${API_URL}/cards`, {
        params: { name: query }
      });
      setResults(res.data);
    }, 200);
  }, [query]);

  // Add card to deck
  const addCard = (card) => {
    setDeck((prev) => {
      const existing = prev.find((c) => c.image_url === card.image_url);
      if (existing) {
        return prev.map((c) =>
          c.image_url === card.image_url ? { ...c, qty: c.qty + 1 } : c
        );
      }
      return [...prev, { ...card, qty: 1 }];
    });
  };

  // Remove card from deck
  const removeCard = (image_url) => {
    setDeck((prev) => {
      const existing = prev.find((c) => c.image_url === image_url);
      if (existing.qty === 1) return prev.filter((c) => c.image_url !== image_url);
      return prev.map((c) =>
        c.image_url === image_url ? { ...c, qty: c.qty - 1 } : c
      );
    });
  };

  // Print
  const handlePrint = () => window.print();

  // Expand deck into individual cards for printing
  const printCards = deck.flatMap((c) => Array(c.qty).fill(c));

  return (
    <div className="app">
      {/* Search UI - hidden on print */}
      <div className="no-print">
        <h1>SVE Proxy Printer</h1>

        {/* Search */}
        <input
          type="text"
          placeholder="Search cards..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />

        {/* Search results dropdown */}
        {results.length > 0 && (
          <div className="results">
            {results.map((card) => (
              <div key={card.image_url} className="result-item" onClick={() => addCard(card)}>
                <img src={card.image_url} alt={card.card_name} width={40} />
                <span>{card.card_name} ({card.set_code}-{card.card_number})</span>
              </div>
            ))}
          </div>
        )}

        {/* Options */}
        <div className="options">
          <label>
            <input type="checkbox" checked={inkSaver} onChange={(e) => setInkSaver(e.target.checked)} />
            Ink-saver mode
          </label>
          <label>
            <input type="checkbox" checked={addSpace} onChange={(e) => setAddSpace(e.target.checked)} />
            Add space between cards
          </label>
        </div>

        {/* Deck list */}
        <div className="deck-list">
          {deck.map((card) => (
            <div key={card.image_url} className="deck-item">
              <img src={card.image_url} alt={card.card_name} width={40} />
              <span>{card.card_name}</span>
              <button onClick={() => removeCard(card.image_url)}>-</button>
              <span>{card.qty}</span>
              <button onClick={() => addCard(card)}>+</button>
            </div>
          ))}
        </div>

        {/* Buttons */}
        <button onClick={handlePrint}>Print</button>
        <button onClick={() => setDeck([])}>Clear</button>
      </div>

      {/* Print grid - only shown on print */}
      <div className={`print-grid ${addSpace ? "with-space" : ""} ${inkSaver ? "ink-saver" : ""}`}>
        {printCards.map((card, i) => (
          <img key={i} src={card.image_url} alt={card.card_name} />
        ))}
      </div>
    </div>
  );
}