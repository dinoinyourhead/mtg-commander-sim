# MTG Commander Sim

Monte Carlo simulation tool for analyzing Magic: The Gathering Commander decks (100 cards).

## Vision

Instead of building a complete MTG rules engine, we use a **tag-based abstraction system**:
- Cards are enriched with functional tags (RAMP, DRAW, REMOVAL)
- A Python state machine simulates thousands of test hands
- LLMs provide strategic decision-making (Phase 4+)

**Goal**: Identify statistical weaknesses (mana screw, missing ramp) through simulation.

## Architecture

```
Phase 1: Setup & Data Fetching ← YOU ARE HERE
Phase 2: Goldfish Engine (State Machine)
Phase 3: Monte Carlo & Statistics
Phase 4: AI Integration (LLM Decision Agent)
Phase 5: Web API & Frontend
```

## Tech Stack

- **Backend**: Python 3.11+, FastAPI
- **Data**: Pydantic, Pandas, NumPy
- **External APIs**: Scryfall (card data)
- **AI**: OpenAI/Anthropic/Gemini (tagging & decisions)

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Quick Start (Phase 1)

```bash
# Test card import
python test_import.py
```

This will load sample cards from `data/sample_decklist.txt` and display their parsed data (name, CMC, tags).

## Project Structure

```
mtg-commander-sim/
├── src/
│   ├── core/           # Core domain logic (models, scryfall, tags)
│   ├── api/            # FastAPI endpoints (Phase 5)
│   └── simulation/     # Monte Carlo simulation (Phase 3)
├── tests/              # Unit & integration tests
├── data/               # Sample decklists
└── test_import.py      # Phase 1 validation script
```

## Development Status

- [x] Phase 1: Setup & Data Fetching
- [ ] Phase 2: Goldfish Engine
- [ ] Phase 3: Monte Carlo Simulation
- [ ] Phase 4: AI Integration
- [ ] Phase 5: Web API & Frontend

## License

MIT
