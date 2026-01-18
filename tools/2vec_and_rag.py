import json
from sentence_transformers import SentenceTransformer
from pinecone import Pinecone


pc = Pinecone(
    api_key="",
)

index_name = "autotranslation"
index = pc.Index(index_name)

def get_model():
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    return model

def get_sentences(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    sentences = [line.strip() + '\n' for line in lines if line.strip()]
    return sentences

def get_embeddings(model, sentences):
    embeddings = model.encode(sentences)
    return embeddings

def prepare_rag_data(sentences, embeddings):
    vectors = []
    for i, (sentence, embedding) in enumerate(zip(sentences, embeddings)):
        vectors.append({
            'id': f"vec{i}",
            'values': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
            'metadata': {'text': sentence}
        })
    return vectors

def main():
    try:
        file_path = r''
        
        model = get_model()
        
        sentences = get_sentences(file_path)
        print(f"Loaded {len(sentences)} sentences")
        if not sentences:
            print("Warning: No sentences were loaded!")
            return
        
        embeddings = get_embeddings(model, sentences)
        
        rag_data = prepare_rag_data(sentences, embeddings)
        
        json_path = r""
        with open(json_path, 'w', encoding='utf-8') as jf:
            json.dump(rag_data, jf, ensure_ascii=False, indent=4)

        batch_size = 100
        for i in range(0, len(rag_data), batch_size):
            batch = rag_data[i:i + batch_size]
            index.upsert(vectors=batch)

        print("Index created successfully!")
        
    except FileNotFoundError as e:
        print(f"Error: Could not find file {file_path}")
        print(f"Full error: {str(e)}")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        import traceback
        print(traceback.format_exc())


if __name__ == '__main__':
    main()