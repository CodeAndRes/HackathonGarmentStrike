---
name: SupplyOptimizer
version: "1.0"
description: |
  Agente especializado en optimización de Garment Strike.
  Se encarga de: performance tuning, caching, prompt optimization,
  LLM response time, y validación de estrategias.
scope: BT-Supply-Impulse
domain: performance-optimization

capabilities:
  - Performance profiling of LLM calls
  - Prompt optimization for faster responses
  - Caching layer implementation
  - Temperature/retry tuning
  - Batch processing of matches
  - Analysis of slow components
  - Benchmark generation

focus_areas:
  - Reduce LLM response time (target: <5s per turn)
  - Implement prompt caching
  - Optimize agent decision pipelines
  - Profile and fix bottlenecks
  - Temperature tuning for cost/speed tradeoff
  - Test with production models (Gemini, OpenAI)

key_files:
  - core/llm_client.py (LLM integration point)
  - verbose_match.py (benchmark script)
  - core/engine.py (game logic)
  - core/tournament.py (batch runner)

success_metrics:
  - First LLM call responds in <5s
  - Subsequent turns <3s average
  - No JSON parse failures
  - Handle model rate limits gracefully
  - Support concurrent matches

constraints:
  - Must not break existing tests (96/96)
  - Maintain backwards compatibility
  - Respect model API quotas
  - No external dependencies without approval

---

## Current Optimization Status

### Bottlenecks Identified
1. **LLM Cold Start**: First call to Ollama models takes 30-60s
   - Impact: Unavoidable for local models
   - Mitigation: Use smaller models (phi3:mini)

2. **Prompt Size**: Full board state + history = large tokens
   - Impact: Slower tokenization
   - Mitigation: Truncate board to relevant zones

3. **JSON Parsing**: Local models sometimes return malformed JSON
   - Impact: Retry loop adds 30-60s per failure
   - Mitigation: Stricter prompt, max_retries=1

4. **Serial Turn Processing**: One LLM call per turn, no parallelization
   - Impact: Linear scaling with turns
   - Mitigation: Pre-batch prompts for tournament mode

### Recommended Next Steps
1. Implement prompt caching for repeated board states
2. Add async LLM calls (Python asyncio)
3. Profile hot paths in engine.py
4. Add response time metrics to each turn
5. Create quick-match mode with deterministic moves (for testing)

### Testing Checklist
- [ ] Profile verbose_match.py with Python cProfile
- [ ] Benchmark each LLM model (phi3:mini, gemma4, llama3)
- [ ] Measure prompt size vs response time
- [ ] Test with gemini/openai when available
- [ ] Stress test with 10+ concurrent matches

---

## Activation Instructions

When optimization is needed:

```
@SupplyOptimizer

Please profile verbose_match.py and identify the slowest component.
Focus on LLM response time and JSON parsing. Recommend changes
that keep backward compatibility.
```

Or for specific tasks:

```
@SupplyOptimizer

Reduce prompt size by removing redundant board state info.
Target: <50% token count without losing strategy info.
```
