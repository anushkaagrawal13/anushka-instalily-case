from vector_manager import live_store

results = live_store.semantic_search_with_intent(
    query="How do I install part PS11752778?",
    intent="installation"
)
print(results)