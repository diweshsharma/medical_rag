import logfire
from sentence_transformers import SentenceTransformer

def embed_chunks(chunks , model_name = "all-MiniLM-L6-v2", batch_size = 64):
    """
    Takes chunks (list of {"page_content": ..., "metadata": ...}),
    embeds each chunk's page_content, and returns the chunks with
    an added "embedding" field ready for indexing into Qdrant.
    """
    with logfire.span("embedding"):
        model = SentenceTransformer(model_name)
        texts = [chunk["page_content"] for chunk in chunks]
        embeddings = model.encode(texts, batch_size = batch_size, show_progress_bar = True )
        
        for chunk , vector in zip(chunks, embeddings):
            chunk['embedding'] = vector.tolist()

        logfire.info("embedded {count}", count=len(chunks))
        return chunks