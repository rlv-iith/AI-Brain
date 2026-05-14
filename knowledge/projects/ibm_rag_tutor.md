# AI Textbook Tutor — IBM SkillBuild Capstone

**Category:** GenAI / RAG Agent  
**Result:** IBM AI Agent Architect certification  
**Stack:** LangChain, OpenAI embeddings, VectorDB, Streamlit

## What it does
A hallucination-free AI tutor that answers questions strictly from uploaded PDF textbooks. Students upload their textbook; the system chunks it, embeds it, and answers questions with exact citations — no making up facts.

## Architecture
1. PDF is chunked into overlapping segments (512 tokens, 64 overlap)
2. Each chunk is embedded with OpenAI `text-embedding-3-small`
3. Stored in a FAISS vector index
4. On query: top-k chunks retrieved, injected into LLM context as grounding
5. LLM instructed to only answer from context; outputs "I don't know" if not found

## Key lesson
RAG is not about making the model smarter — it's about giving it the right evidence at inference time. The quality of the chunking strategy matters more than the model size.
