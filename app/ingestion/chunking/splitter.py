from anthropic import __name
import logfire 
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunking(docs):
    """load documents and split them into chunks """
    with logfire.span("chunking"):
        splitter = RecursiveCharacterTextSplitter(
            separators =["\n\n" , "\n" , " ", ""],
            chunk_size = 1000,
            chunk_overlap = 200,

        )

        all_chunks = []
        for doc in docs:
            splits = splitter.split_text(doc.page_content)

            for i, split_text in enumerate(splits):
                chunk_metadata = dict(doc.metadata)
                chunk_metadata['chunk_index'] = i
                chunk_metadata["chunk_id"] = f"{doc.metadata.get('id')}_{i}"
                chunk_metadata["total_chunks"] = len(splits)

                all_chunks.append({
                    "page_content": split_text,
                    "metadata": chunk_metadata,
                    
                })
        logfire.info("Number of chunks: {count}", count=len(all_chunks))
        return all_chunks
        

